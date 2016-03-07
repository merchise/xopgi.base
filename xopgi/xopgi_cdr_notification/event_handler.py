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

from openerp import api, fields, models
from openerp.addons.xopgi_cdr.cdr_agent import event_raise
from xoeuf import signals

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
    subscribed_events = fields.Many2many('cdr.system.event')
    action = fields.Selection([(k, v['name']) for k, v in ACTIONS.items()])
    recipients = fields.Many2many('res.users',
                                  'cdr_notification_recipients_rel',
                                  'handler_id', 'user_id')
    mail_template = fields.Many2one('email.template',
                                    context={'thread_model': _name,
                                             'default_use_default_to': True})
    notification_text = fields.Text()
    active = fields.Boolean(default=True)

    def do_mail_notify(self):
        self.mail_template.send_mail(self.id)

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
            res.update(
                partner_ids=partner_ids,
                email_to=False,
                email_cc=False
            )
        return res
