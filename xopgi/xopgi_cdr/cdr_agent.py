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
Deferred = DeferredType(queue=queue('cdr'), expires=65, retry=False)


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
        Cycle = self.env['cdr.evaluation.cycle']
        return Deferred(Cycle.create)


class CYCLE_STATE(enum.Enum):
    CREATED = 0
    STARTED = 1
    ABORTED = 2
    DONE = 3


DEFAULT_CYCLE_STATE = CYCLE_STATE.CREATED


class EvaluationCycle(models.Model):
    _name = 'cdr.evaluation.cycle'

    state = fields.Enumeration(
        CYCLE_STATE,
        default=DEFAULT_CYCLE_STATE,
        force_char_column=True
    )

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, values=None, vars_to_evaluate=None,
               evidences_to_evaluate=None):
        '''Add new cdr.evaluation.cycle.

        Evaluates events that must be evaluated by schedule or
        cdr.control.variable and cdr.evidences passed as params.

        :param values: original method param that is ignore

        :param vars_to_evaluate: cdr.control.variable recordset to evaluate

        :param evidences_to_evaluate: cdr.evidences recordset to evaluate

        '''
        cycle = super(EvaluationCycle, self).create({})
        if vars_to_evaluate or evidences_to_evaluate:
            if vars_to_evaluate:
                vars_to_evaluate.evaluate(cycle)
            if evidences_to_evaluate:
                valid_var = (lambda var: not (vars_to_evaluate and
                                              var in vars_to_evaluate))
                for evidence in evidences_to_evaluate:
                    evidence.control_vars.filtered(valid_var).evaluate(cycle)
                evidences_to_evaluate.evaluate(cycle)
        else:
            # Look for events that have the next_call less than the same as
            # the creation date of the last cycle that was created. The
            # next_call of events is updated when an event is evaluated.
            # To see function evaluate for BasicEvent and RecurrentEvent.
            # --The next_call conditions events to be evaluated or not!!.
            events = self.env['cdr.system.event'].search(
                [('next_call', '<=', cycle.create_date)]
            )
            events.evaluate(cycle)
        cycle.state = CYCLE_STATE.DONE
        return cycle
