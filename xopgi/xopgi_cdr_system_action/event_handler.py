# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr.event_handler
# ---------------------------------------------------------------------
# Copyright (c) 2016 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-04-10

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from openerp import api, exceptions, fields, models, _
from openerp.addons.xopgi_cdr.cdr_agent import EVENT_SIGNALS
from xoeuf import signals


ACTION_SERVER_MODEL_NAME = 'ir.actions.server'


class EventHandler(models.Model):
    _name = 'cdr.event.action.handler'

    name = fields.Char(translate=True, required=True)
    subscribed_events = fields.Many2many('cdr.system.event')
    action = fields.Many2one('ir.actions.server', required=True)
    active = fields.Boolean(default=True)
    event_raise = fields.Boolean(default=True)
    continue_raising = fields.Boolean(default=True)
    stop_raising = fields.Boolean()

    @signals.receiver(EVENT_SIGNALS.values())
    def do_action(self, signal):
        '''Execute action method of each handler subscribed to any of
        raising events.

        '''
        actions = self.env[ACTION_SERVER_MODEL_NAME]
        for handler in self.env['cdr.event.action.handler'].search(
                [('subscribed_events', 'in', self.ids),
                 (signal.action, '=', True)]):
            if handler.action:
                actions += handler.action
        actions.run()

    @api.constrains('event_raise', 'continue_raising', 'stop_raising')
    def _check_signals(self):
        if not all(h.event_raise or h.continue_raising or h.stop_raising
                   for h in self):
            raise exceptions.ValidationError(
                _('At least one signal must be checked.'))
