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


#  TODO: move to a new module.
class EventHandler(models.Model):
    ''' Generic cdr event definition. For specifics cdr events
    implementations just need to inherit by delegation of this model and
    override evaluate method.

    Recommendation: define _description for specific event implementations
    to allow correct user identification.

    '''
    _name = 'cdr.event.basic.handler'
    _description = "Generic CDR event handler"

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
            domain = evaluate(self.env, domain, mode='exec')
        else:
            domain = evaluate(self.env, domain)
        return domain

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
#  env are able to use.''')

    def get_recipients(self):
        for handler in self:
            domain = handler.get_domain()
            handler.recipients = self.env['res.users'].search(domain)

    def do_chat_notify(self):
        for recipient in self.recipients:
            # override self to get recipient right lang translation
            self = self.with_context(lang=recipient.lang)
            session_id = self.env['im_chat.session'].search(
                [('user_ids', '=', recipient.id)]).filtered(
                lambda s: len(s.user_ids) == 1)
            if not session_id:
                session_id = self.env['im_chat.session'].create(
                    {'user_ids': [(6, 0, recipient.ids)]})
            notification_text = "%s: \n%s" % (
                _({k: v for k, v in PRIORITIES}[self.priority]),
                self.notification_text)
            self.env['im_chat.message'].post(False, session_id[0].uuid,
                                             'meta', notification_text)

    def do_js_notify(self):
        self.env['cdr.js.notification'].send(
            handler_id=self.id, recipients=self.recipients)

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

    @api.multi
    def message_get_default_recipients(self):
        '''This method is used to get the default recipients of the mail
        notification. It is called from email.template model.

        '''
        res = {}
        for handler in self:
            partner_ids = [user.partner_id.id
                           for user in handler.recipients
                           if user.partner_id]
            res[handler.id] = dict(
                partner_ids=partner_ids,
                email_to=False,
                email_cc=False
            )
        return res


class JSNotification(models.TransientModel):
    _name = 'cdr.js.notification'

    handler_id = fields.Many2one('cdr.event.basic.handler', required=True)
    title = fields.Char(related='handler_id.name')
    message = fields.Text(related='handler_id.notification_text')
    priority = fields.Selection(PRIORITIES, related='handler_id.priority')
    user_id = fields.Many2one('res.users')
    state = fields.Selection([('new', 'New'), ('open', 'Open')], default='new')

    def __init__(self, pool, cr):
        super(JSNotification, self).__init__(pool, cr)
        #  Ensure 24 hours of js notifications life time.
        JSNotification._transient_max_hours = 24
        JSNotification._transient_max_count = None

    def send(self, handler_id, recipients):
        #  Only create if it not exist.
        self.search([('handler_id', '=', handler_id),
                     ('user_id', 'not in', recipients.ids)]).unlink()
        for user in recipients:
            self.create_or_renew(handler_id, user.id)

    def create_or_renew(self, handler_id, user_id):
        res = self.search([('handler_id', '=', handler_id),
                           ('user_id', '=', user_id)])
        if res and res.state != 'new':
            res.state = 'new'
        return res or self.create(dict(handler_id=handler_id, user_id=user_id))

    @api.model
    def get_notifications(self):
        notifications = self.search([('user_id', '=', self._uid)])
        priority = {k: v for k, v in PRIORITIES}
        res = [{'title': item.title, 'message': item.message,
                'priority': item.priority,
                'label': _(priority.get(item.priority, 'Information'))}
               for item in notifications]
        notifications.write({'state': 'open'})
        return res
