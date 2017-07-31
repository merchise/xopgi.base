# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr.cdr_agent
# ---------------------------------------------------------------------
# Copyright (c) 2016-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-02-13

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoeuf.odoo import api, models
from xoeuf.odoo.jobs import DeferredType, queue
from xoeuf.signals import Signal
from xoutil import logger


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


class EvaluationCycle(models.Model):
    _name = 'cdr.evaluation.cycle'

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

        res = super(EvaluationCycle, self).create({})
        if vars_to_evaluate or evidences_to_evaluate:
            if vars_to_evaluate:
                vars_to_evaluate.evaluate(res)
            if evidences_to_evaluate:
                valid_var = (lambda var: not (vars_to_evaluate and
                                              var in vars_to_evaluate))
                for evidence in evidences_to_evaluate:
                    evidence.control_vars.filtered(valid_var).evaluate(res)
                evidences_to_evaluate.evaluate(res)
        else:
            # Look for events that have the next_call less than the same as
            # the creation date of the last cycle that was created. The
            # next_call of events is updated when an event is evaluated.
            # To see function evaluate for BasicEvent and RecurrentEvent.
            # --The next_call conditions events to be evaluated or not!!.
            events = self.env['cdr.system.event'].search(
                [('next_call', '<=', res.create_date)]
            )
            events.evaluate(res)
            for signal in EVENT_SIGNALS:
                # Not use groupby because a recordset is needed on
                # signaling send.
                sender = events.filtered(lambda event: event.action == signal)
                if sender:
                    logger.debug(
                        'Sending signal (%s) for Events: (%s)',
                        signal,
                        ', '.join(e.name for e in sender)
                    )
                    EVENT_SIGNALS[signal].send(sender=sender)
        return res
