# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr.system_event
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

from datetime import timedelta, datetime
from openerp import api, exceptions, fields, models, _
from xoeuf.tools import str2dt
from xoutil import logger
from .cdr_agent import EVENT_SIGNALS
from .util import evaluate, get_free_names

EVENT_STATES = [
    ('raising', 'Raising'),
    ('not_raising', 'Not raising')
]


class SystemEvent(models.Model):
    ''' Generic cdr event definition. For specifics cdr events
    implementations just need to inherit by delegation of this model and
    override evaluate method.

    Recommendation: define _description for specific event implementations
    to allow correct user identification.

    '''

    _name = 'cdr.system.event'
    _description = "Generic CDR event"

    _order = 'priority'

    name = fields.Char(translate=True)
    definition = fields.Char(
        required=True, help="Python expression combining controls "
                            "variables operators and literal values.\n"
                            "Eg: var1 - var2 > (var3 or 400) \n"
                            "The result will be evaluate as boolean value.")
    next_call = fields.Datetime(default=fields.Datetime.now())
    priority = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    evidences = fields.Many2many('cdr.evidence',
                                 'event_evidence_rel',
                                 'event_id',
                                 'evidence_id',
                                 compute='get_evidences', store=True)
    specific_event = fields.Reference([], compute='_get_specific_event')
    state = fields.Selection(EVENT_STATES)
    action = fields.Selection([(k, k.replace('_', ' ').capitalize())
                               for k in EVENT_SIGNALS.keys()] +
                              [('do_nothing', 'Do nothing')],
                              string="Last action")

    def get_specific_event_models(self):
        '''Get models that look like specific event.

        '''
        result = []
        for model_name in self.pool.obj_list():
            model = self.env[model_name]
            if 'cdr.system.event' in getattr(model, '_inherits', {}):
                result.append(model)
        return result

    def _get_specific_event(self):
        '''Get specific event reference from it's generic one.

        '''
        for event in self:
            for model in self.get_specific_event_models():
                field = model._inherits.get('cdr.system.event')
                result = model.search([(field, '=', event.id)], limit=1)
                if result:
                    event.specific_event = "%s,%d" % (result._name, result.id)

    @api.depends('definition')
    @api.onchange('definition')
    def get_evidences(self):
        '''Get evidences referenced on event definition.

        '''
        evidences = self.env['cdr.evidence']
        for event in self:
            if event.active and event.definition:
                domain = [
                    ('name', 'in', tuple(get_free_names(event.definition)))]
                event.evidences = evidences.search(domain)
            else:
                event.evidences = evidences

    def _get_vars_to_evaluate(self):
        res = self.env['cdr.control.variable']
        for event in self:
            for evidence in event.evidences:
                res += evidence.control_vars
        return res

    def _get_evidences_to_evaluate(self):
        res = self.env['cdr.evidence']
        for event in self:
            res += event.evidences
        return res

    def evaluate_dependences(self, cycle):
        self._get_vars_to_evaluate().evaluate(cycle)
        self._get_evidences_to_evaluate().evaluate(cycle)

    def _evaluate(self):
        return evaluate(self.definition, **self.evidences.get_bool_value())

    @api.constrains('definition')
    def check_definition(self):
        try:
            self._evaluate()
        except Exception, e:
            raise exceptions.ValidationError(
                _("Wrong definition: %s") % e.message)

    def evaluate(self, cycle):
        self.evaluate_dependences(cycle)
        for event in self:
            # call specific event evaluate method to get each
            # corresponding behavior.
            event.specific_event.evaluate(cycle)


class BasicEvent(models.Model):
    _name = 'cdr.basic.event'
    _description = "Basic CDR event"

    _inherits = {'cdr.system.event': 'event_id'}

    event_id = fields.Many2one('cdr.system.event',
                               required=True, ondelete='cascade')
    interval = fields.Float(required=True,
                            help="Time (in hours:minutes format) between "
                                 "evaluations.")
    time_to_wait = fields.Float(
        required=True, help="Time (in hours:minutes format) getting "
                            "consecutive positive evaluations before raise.")
    times_to_raise = fields.Integer()

    @api.depends('interval')
    def get_next_call(self):
        '''Compute the next evaluation date.

        '''
        for event in self:
            if event.active and event.interval:
                event.next_call = datetime.now() + timedelta(
                    hours=event.interval)
            else:
                event.next_call = False

    def update_event(self, value, cycle):
        next_call = str2dt(cycle.create_date) + timedelta(hours=self.interval)
        times_to_raise = ((self.time_to_wait / self.interval)
                          if not value else self.times_to_raise - 1)
        state = 'raising' if value and times_to_raise < 1 else 'not_raising'
        if self.state == 'raising':
            action = 'continue_raising' if state == 'raising' else 'stop_raising'
        else:
            action = 'raise' if state == 'raising' else 'do_nothing'
        values = dict(next_call=next_call, state=state, action=action)
        self.write(values)

    def evaluate(self, cycle):
        try:
            value = self.event_id._evaluate()
        except Exception, e:
            logger.exception('Error evaluating event %s defined as: ',
                             (self.name, self.definition))
            logger.exception(e)
            return None
        else:
            self.update_event(value, cycle)


class RecurrentEvent(models.Model):
    _name = 'cdr.recurrent.event'
    _description = "Recurrent CDR event"

    _inherits = {'cdr.system.event': 'event_id'}

    event_id = fields.Many2one('cdr.system.event',
                               required=True, ondelete='cascade')
    time = fields.Float()
    recurrence = fields.Many2one('recurrent.model', required=True,
                                 delegate=True, ondelete='cascade')

    def update_event(self, value):
        next_call = self.recurrence.next_date(self.recurrence.rrule)
        state = 'raising' if value else 'not_raising'
        action = 'raise' if state == 'raising' else 'do_nothing'
        values = dict(next_call=next_call, state=state, action=action)
        self.write(values)

    def evaluate(self, cycle):
        try:
            value = self.event_id._evaluate()
        except Exception, e:
            logger.exception('Error evaluating event %s defined as: ',
                             (self.name, self.definition))
            logger.exception(e)
            return None
        else:
            self.update_event(value)

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        if any(field in self.recurrence._fields for field in vals):
            vals.update(is_recurrent=True)
        return super(RecurrentEvent, self).create(vals)
