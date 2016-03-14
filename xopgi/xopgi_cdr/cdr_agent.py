# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr.cdr_agent
# ---------------------------------------------------------------------
# Copyright (c) 2016 Merchise Autrement and Contributors
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

from openerp import api, models
from xoeuf.signals import Signal
from xoutil import logger


event_raise = Signal('event', '''
    Signal sent to notify some system event raising.

    Arguments:

    :param sender: 'cdr.system.event' recordset of events are raising.

''')


class CDRAgent(models.Model):
    _name = 'cdr.agent'

    @api.model
    def new_evaluation_cycle(self):
        # TODO: do this on celery task.
        return self.env['cdr.evaluation.cycle'].create()


class EvaluationCycle(models.Model):
    _name = 'cdr.evaluation.cycle'

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, values=None, vars_to_evaluate=None):
        ''' To force evaluation of some variable(s) pass varible names on
        vars_to_evaluate param as tuple.

        :param values: original method param that is ignore
        :param vars_to_evaluate: tuple of variable's name to force evaluate

        '''
        res = super(EvaluationCycle, self).create({})
        if vars_to_evaluate:
            # TODO: Evaluate passed variables
            return res
        else:
            events = self.env['cdr.system.event'].search(
                [('next_call', '<=', res.create_date)])
            events_to_raise = events.get_events_to_raise(res)
            if events_to_raise:
                logger.debug('Raising Events: %s' % (', '.join(
                    [e.name for e in events_to_raise])))
                event_raise.send(sender=events_to_raise)
        return res
