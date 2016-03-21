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
from openerp.addons.xopgi_cdr.cdr_agent import event_raise
from openerp.addons.xopgi_cdr.util import evaluate
from xoeuf import signals
from .res_config import TEMPLATES

ACTIONS = {
    'mail': dict(
        name='Mail Notification', action='do_mail_notify'),
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

    name = fields.Char(translate=True)
    priority = fields.Selection(TEMPLATES, default=TEMPLATES[0][0],
                                required=True)
    subscribed_events = fields.Many2many('cdr.system.event')
    action = fields.Selection([(k, v['name']) for k, v in ACTIONS.items()])
    recipients = fields.Many2many('res.users',
                                  'cdr_notification_recipients_rel',
                                  'handler_id', 'user_id',
                                  compute='get_recipients')
    domain = fields.Text(
        help='Odoo domain to search recipients.',
        default='''
        #  Odoo domain like: [('field_name', 'operator', value)]
        #  or python code to return on result var a odoo domain like
        #  if uid != 1:
        #      result = [('id', '=', uid)]
        #  else:
        #      result = [('id', '!=', 1)]
        #  self, env, model, context and group are able to use:
        #  self => active model (on new api).
        #  context => active context.''')
    notification_text = fields.Text(translate=True, required=True)
    active = fields.Boolean(default=True)

    def get_recipients(self):
        if not self.domain or self.domain.strip().startswith('['):
            domain = evaluate(self.env, self.domain or '[]')
        else:
            domain = evaluate(self.env, self.domain, mode='exec')
        return self.env['res.users'].search(domain)

    def do_mail_notify(self):
        template_id = self.env[
            'xopgi.cdr.notification.config'].get_res_id(self.priority)
        self.pool['email.template'].send_mail(
            self._cr, self._uid, template_id, self.id,
            context=dict(self._context, tpl_force_default_to=True))

    def do_chat_notify(self):
        notification_text = "%s: \n%s" % (
            _(ACTIONS[self.priority]['name']), self.notification_text)
        session_id = self.env['im_chat.session'].search(
            [('user_ids', '=', i) for i in self.recipients.ids]).filtered(
            lambda s: len(s.user_ids) == len(self.recipients))
        if not session_id:
            session_id = self.env['im_chat.session'].create(
                {'user_ids': [(6, 0, self.recipients.ids)]})
        self.env['im_chat.message'].post(False, session_id[0].uuid, 'meta',
                                         notification_text)

    def do_js_notify(self):
        template_id = self.env['xopgi.cdr.notification.config'].get_res_id(
            self.priority)
        notification_text = self.pool['email.template'].generate_email_batch(
            self._cr, self._uid, template_id, res_ids=[self.id],
            fields=['body_html'], context=self._context)[self.id]['body']
        # TODO: show notification
        return notification_text

    @signals.receiver(event_raise)
    def do_notify(self, signal):
        '''Execute action method of each handler subscribed to any of
        raising events.

        '''
        for handler in self.env['cdr.event.basic.handler'].search(
                [('subscribed_events', 'in', self.ids)]):
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

    @api.model
    def _get_access_link(self, mail, partner):
        return self.env['mail.thread']._get_access_link(mail, partner)
