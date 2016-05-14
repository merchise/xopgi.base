# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr.event_handler
# ---------------------------------------------------------------------
# Copyright (c) 2016 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-02-29

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from openerp import api, fields, models, _
from openerp.addons.xopgi_cdr.cdr_agent import EVENT_SIGNALS
from openerp.addons.xopgi_cdr.util import evaluate
from xoeuf import signals

PRIORITIES = [('info', 'Information'), ('alert', 'Alert'), ('alarm', 'Alarm')]

ACTIONS = {
    'js': dict(
        name='Visual Notification', action='do_js_notify'),
    'chat': dict(
        name='Chat Notification', action='do_chat_notify'),
}


get_method = lambda action: ACTIONS[action]['action']


class EventHandler(models.Model):
    _name = 'cdr.event.basic.handler'

    name = fields.Char(translate=True, required=True)
    priority = fields.Selection(PRIORITIES, default=PRIORITIES[0][0],
                                required=True)
    subscribed_events = fields.Many2many('cdr.system.event')
    action = fields.Selection([(k, v['name']) for k, v in ACTIONS.items()])
    recipients = fields.Many2many('res.users', compute='get_recipients')
    use_domain_builder = fields.Boolean(default=True)
    domain = fields.Text(help='Odoo domain to search recipients.')
    build_domain = fields.Char(help='Odoo domain to search recipients.',
                               string='Domain')
    notification_text = fields.Text(translate=True, required=True)
    active = fields.Boolean(default=True)
    event_raise = fields.Boolean(default=True)
    continue_raising = fields.Boolean(default=True)
    stop_raising = fields.Boolean()

    def get_domain(self):
        domain = self.domain or self.build_domain
        if not domain or all(l.strip().startswith('#')
                             for l in domain.splitlines()
                             if l.strip()):
            domain = []
        elif any(l.strip().startswith('result')
                 for l in domain.splitlines()):
            domain = evaluate(domain, mode='exec', env=self.env, uid=self._uid)
        else:
            domain = evaluate(domain, env=self.env, uid=self._uid)
        return domain

    @api.depends('domain', 'action', 'active', 'notification_text',
                 'subscribed_events')
    def reset_js_notifications(self):
        # remove related notifications when handler change.
        self.env['cdr.js.notification'].search(
            [('handler_id', 'in', self.ids)]).unlink()

    @api.onchange('use_domain_builder')
    def onchange_use_domain_builder(self):
        if self.use_domain_builder:
            domain = self.get_domain()
            domain = (str(domain) if domain else '')
            self.build_domain = domain
            self.domain = ''
        else:
            self.domain = (self.build_domain or '') + _('''
#  Odoo domain like: [('field_name', 'operator', value)]
#  or python code to return on result var a odoo domain like
#  if uid != 1:
#      result = [('id', '=', uid)]
#  else:
#      result = [('id', '!=', 1)]
#  env and uid are able to use.''')

    def get_recipients(self):
        for handler in self:
            domain = handler.get_domain()
            handler.recipients = self.env['res.users'].search(domain)

    def do_chat_notify(self):
        vigilant = self.env.ref('xopgi_cdr_notification.vigilant_user')
        session_ids = self.env['im_chat.session'].search(
            [('user_ids', '=', vigilant.id)])
        for recipient in self.recipients:
            # override self to get recipient right lang translation
            self = self.with_context(lang=recipient.lang)
            session_id = session_ids.filtered(
                lambda s: recipient in s.user_ids and len(s.user_ids) == 2)
            if not session_id:
                session_id = self.env['im_chat.session'].create(
                    {'user_ids': [(6, 0, (recipient.id, vigilant.id))]})
            notification_text = "%s: \n%s" % (
                _({k: v for k, v in PRIORITIES}[self.priority]),
                self.notification_text)
            self.env['im_chat.message'].post(vigilant.id, session_id[0].uuid,
                                             'meta', notification_text)

    def do_js_notify(self):
        notification = self.env['xopgi.web.notification']
        title = u"""
        <span class="e_cdr_{priority}">
          {label}:
        </span>
        {name}
        """
        for user in self.recipients:
            notification.notify(
                uid=user.id,
                id='cdr_handler_%s' % self.id,
                title=title.format(
                    priority=self.priority,
                    label=_({k: v for k, v in PRIORITIES}[self.priority]),
                    name=self.name),
                body=self.notification_text)

    @signals.receiver(EVENT_SIGNALS.values())
    def do_notify(self, signal):
        '''Execute action method of each handler subscribed to any of
        raising events.

        '''
        for handler in self.env['cdr.event.basic.handler'].search(
                [('subscribed_events', 'in', self.ids),
                 (signal.action, '=', True)]):
            action_method = getattr(handler, get_method(handler.action),
                                    NotImplemented)
            action_method()
