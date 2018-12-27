#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

import enum

from xoeuf import api, fields, models
from xoeuf.odoo.jobs import DeferredType, queue
from xoeuf.signals import Signal

import logging
logger = logging.getLogger(__name__)
del logging


# The CDR will use a dedicated queue (you should use a single worker).
#
# Since a new CDR cycle is issued at a 60s rate, waiting longer than 65s,
# would only server to create a backlog of jobs that just do the same.  So
# jobs expire after 65s in the queue.  Also retrying is not needed for the
# same reason.
#
# Also notice that CDRTransientJob allows nested creation of jobs.  This is
# because we need to avoid unending runs of the CDR.  If we simply execute the
# chains as planned, new plans will be schedule at each minute mark; and the
# CDR will be running at all times.  So we make the agent to work in two
# steps: the new_evaluation_cycle that simply schedules a new cycle, which
# expires after 65s; and this method, when execute, schedules the entire plan.
CDRTransientJob = DeferredType(
    queue=queue('cdr'),
    expires=65,
    retry=False,
    allow_nested=True,
)
CDRJobSignature = DeferredType(queue=queue('cdr'), return_signature=True)


EVENT_SIGNALS = {
    'raise': Signal('event_raise', '''
        Signal sent to notify some system event raising.

        Arguments:

        :param sender: 'cdr.system.event' recordset of events are raising.

    '''),
    'continue_raising': Signal('continue_raising', '''
        Signal sent to notify some system event continue raising.

        Arguments:

        :param sender: 'cdr.system.event' recordset of events are continuing raise.

    '''),
    'stop_raising': Signal('stop_raising', '''
        Signal sent to notify some system event stop raising.

        Arguments:

        :param sender: 'cdr.system.event' recordset of events are stoping raise.

    ''')
}


class CDRAgent(models.TransientModel):
    _name = 'cdr.agent'

    @api.model
    def new_evaluation_cycle(self):
        return CDRTransientJob(self._new_evaluation_cycle)

    @api.model
    def _new_evaluation_cycle(self):
        # If a recent cycle is not yet DONE, defer the creation of a new
        # cycle.  This is just a counter measure to avoid possible
        # concurrency.  We cannot be sure the cycle is actually running (it
        # may have stopped forcibly and not signaled); that's why we keep a
        # "small window" of 15 minutes.
        self.env.cr.execute(
            '''SELECT id FROM cdr_evaluation_cycle
               WHERE state != 'DONE' AND state != 'DONE_WITH_ERRORS'
                     AND create_date >= (now() at time zone 'UTC') - '15 minutes'::interval
               LIMIT 1;
            '''
        )
        rows = self.env.cr.fetchall()
        Cycle = self.env['cdr.evaluation.cycle']
        if not rows:
            cycle = Cycle.create({})
            cycle.state = CYCLE_STATE.STARTED
            # I should send the evaluation plan after commiting the new cycle to
            # the CDR, otherwise there's a chance to start a job without the cycle
            # in the DB yet.  But that, requires me to create a new environment.
            cycle_id = cycle.id
            args = self.env.args

            def start():
                with api.Environment.manage():
                    env = api.Environment(*args)
                    Cycle = env['cdr.evaluation.cycle']
                    cycle = Cycle.browse(cycle_id)
                    cycle._create_evaluation_plan().delay()

            self.env.cr.after('commit', start)
            return cycle
        else:
            return Cycle.browse(int(rows[0][0]))


class CYCLE_STATE(enum.Enum):
    #: The cycle was created but computation has not started
    CREATED = 0

    #: The cycle was has created the computation plan.  The computation
    #: may has not started, but the jobs were issued.
    STARTED = 1

    #: Some of the jobs has detected errors.  The cycle may still be running.
    ERRORED = 2

    #: The cycle ended without errors.
    DONE = 3

    #: The cycle ended with errors
    DONE_WITH_ERRORS = 4


DEFAULT_CYCLE_STATE = CYCLE_STATE.CREATED


class EvaluationCycle(models.Model):
    _name = 'cdr.evaluation.cycle'

    state = fields.Enumeration(
        CYCLE_STATE,
        default=DEFAULT_CYCLE_STATE,
        force_char_column=True
    )

    @api.requires_singleton
    def signal_error(self):
        self.state = CYCLE_STATE.ERRORED

    @api.requires_singleton
    def signal_done(self):
        if self.state not in (CYCLE_STATE.ERRORED, CYCLE_STATE.DONE_WITH_ERRORS):
            self.state = CYCLE_STATE.DONE
        else:
            self.state = CYCLE_STATE.DONE_WITH_ERRORS

    @api.requires_singleton
    def _create_evaluation_plan(self, group=None, chain=None, signature=None):
        '''Create a Celery signature representing the entire evaluation plan.

        The current implementation simply creates a Celery group with jobs to
        compute each variable.  Each variable job has a link to the evidences
        they update; and each evidence in turn has a link to the event they
        update.

        Notice that this can make the same evidence and event to be computed
        more than once for the same cycle.

        `group`, `chain` and `signature` are provided to customize the
        creation of the Celery groups, chains and signatures.  For instance,
        you can create a plan that runs in-process and not in celery at all.
        See the `Group`:class:, `Sequence`:class:, and `Task`:class: below for
        API and suitable examples.

        '''
        # See the ADR 'docs/source/adrs/2018-12-32-new-evaluation-cycle.rst'
        #
        # Create a couple inverse mappings from variables to evidences, and
        # from evidences to events.  Then use those to create the jobs and
        # their links.
        if group is None:
            # Celery's group does not protect it from grouping single-jobs.
            def group(*jobs):
                from celery import group as _group
                if len(jobs) > 1:
                    return _group(*jobs)
                else:
                    return jobs[0]

        if chain is None:
            from celery import chain
        if signature is None:
            signature = CDRJobSignature

        def evaljob(obj):
            return signature(obj.evaluate, self.id).on_error(
                signature(self.signal_error)
            )

        def create_event_job(event):
            return signature(event.evaluate, self.id)

        # We don't really care about "sharing" the same signature for events
        # and evidences job; they will be duplicated anyways.
        def create_evidence_job(evidence):
            events = evidencesmap[evidence]
            jobs = [create_event_job(event) for event in events]
            return chain(evaljob(evidence), group(*jobs))

        def create_variable_job(var):
            evidences = varsmap[var]
            jobs = [create_evidence_job(ev) for ev in evidences]
            return chain(evaljob(var), group(*jobs))

        events = self._get_events_to_update()
        varsmap = {}
        evidencesmap = {}
        for event in events:
            evidences = event._get_evidences_to_evaluate()
            for evidence in evidences:
                events = evidencesmap.setdefault(evidence, [])
                events.append(event)
                for var in evidence.control_vars:
                    evs = varsmap.setdefault(var, [])
                    evs.append(evidence)
        jobs = [create_variable_job(var) for var in varsmap]
        # I want the signal_done job to be executed after the entire cycle is
        # done, even in the case of errors.  Otherwise, the cycle will remain
        # in the ERRORED state, but I want it to be in DONE_WITH_ERRORS.
        if jobs:
            return chain(
                group(*jobs).on_error(signature(self.signal_done)),
                signature(self.signal_done)
            )
        else:
            return signature(self.signal_done)

    @api.requires_singleton
    def _get_events_to_update(self):
        # Look for events that have the next_call less than the same as the
        # creation date of the last cycle that was created. The next_call of
        # events is updated when an event is evaluated.  See function evaluate
        # for BasicEvent and RecurrentEvent.
        events = self.env['cdr.system.event'].search(
            [('next_call', '<=', self.create_date)]
        )
        return events

    @api.model
    def create_and_evaluate(self, values=None, variables=None,
                            evidences=None):
        '''Create a cycle and evaluate it on-line.

        This does not issue any Celery job.  If variables is not None, compute
        only the variables passed.  If evidences is not None, compute only the
        evidences passed.  If both are passed, we evaluate the variables first
        and then the evidences.  If both are None, the full plan is evaluated
        on-line.

        '''
        res = self.create(values or {})
        if variables:
            variables.evaluate(res)
        if evidences:
            evidences.evaluate(res)
        if not variables and not evidences:
            plan = res._create_evaluation_plan(
                group=Group,
                chain=Sequence,
                signature=SavepointTask,
            )
            plan()
        return res


class Signature(object):
    def on_error(self, signature):
        return OnError(self, signature)


class Sequence(Signature):
    '''Mock to run chains on-line.'''

    def __init__(self, *subtasks):
        self.subtasks = subtasks

    def __call__(self, *args, **kwargs):
        for subtask in self.subtasks:
            res = subtask(*args, **kwargs)
            args = (res, )
            kwargs = {}
        return res

    def __repr__(self):
        subtasks = ', '.join(map(repr, self.subtasks))
        return "<Sequence({subtasks})>".format(subtasks=subtasks)


class Group(Signature):
    '''Mock to run groups on-line.'''

    def __init__(self, *subtasks):
        self.subtasks = subtasks

    def __call__(self, *args, **kwargs):
        results = []
        for subtask in self.subtasks:
            results.append(subtask(*args, **kwargs))
        return results

    def __repr__(self):
        subtasks = ', '.join(map(repr, self.subtasks))
        return "<Group({subtasks})>".format(subtasks=subtasks)


class Task(Signature):
    '''Mock to run jobs on-line'''
    def __init__(self, method, *args, **kwargs):
        self.method = method
        self.signature_args = args
        self.signature_kwargs = kwargs

    def __call__(self, *args, **kwargs):
        # CDRJobSignature is immutable, we must ignore the passed *args, and
        # **kwargs to be compatible.
        args = self.signature_args
        kwargs = self.signature_kwargs
        print('Calling {method} with *{args} and **{kwargs}'.format(
            method=self.method,
            args=args,
            kwargs=kwargs,
        ))
        return self.method(*args, **kwargs)


class OnError(Signature):
    def __init__(self, subtask, handler):
        self.subtask = subtask
        self.handler = handler

    def __call__(self, *args, **kwargs):
        try:
            return self.subtask(*args, **kwargs)
        except Exception:
            return self.handler()


class SavepointTask(Task):
    '''Mock but run the task within a savepoint if possible.'''
    def __init__(self, method, *args, **kwargs):
        super(SavepointTask, self).__init__(method, *args, **kwargs)
        owner = getattr(method, '__self__', getattr(method, 'im_self', None))
        if owner and isinstance(owner, models.BaseModel):
            self.owner = owner
        else:
            self.owner = None

    def __call__(self, *args, **kwargs):
        super_ = super(SavepointTask, self).__call__
        if self.owner:
            with self.owner.env.cr.savepoint():
                return super_(*args, **kwargs)
        else:
            return super_(*args, **kwargs)
