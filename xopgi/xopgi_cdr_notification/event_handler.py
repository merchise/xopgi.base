# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr.event_handler
# ---------------------------------------------------------------------
# Copyright (c) 2016-2017 Merchise Autrement [~º/~] and Contributors
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

from xoeuf.odoo import api, fields, models, _
from xoeuf.odoo.exceptions import ValidationError
from xoeuf.odoo.addons.xopgi_cdr.cdr_agent import EVENT_SIGNALS
from xoeuf.odoo.addons.xopgi_cdr.util import evaluate
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
    '''This model allows you to configure an notification when a certain event
    occurs.

    '''
    _name = 'cdr.event.basic.handler'

    name = fields.Char(
        translate=True,
        required=True,
        help='Name of handler basic event'
    )

    priority = fields.Selection(
        PRIORITIES,
        default=PRIORITIES[0][0],
        required=True,
        help='Select to specify the priority of the notification'
    )

    subscribed_events = fields.Many2many(
        'cdr.system.event'
    )

    action = fields.Selection(
        [(k, v['name']) for k, v in ACTIONS.items()],
        help='Select to specify the medium by which the notification'
             ' is to be displayed'
    )

    recipients = fields.Many2many(
        'res.users',
        compute='get_recipients',
        help='Recipients under the result of the domain'

    )

    use_domain_builder = fields.Boolean(
        default=True,
        help='Use or not builder domain'
    )

    domain = fields.Text(
        help='Odoo domain to search recipients.'
    )

    build_domain = fields.Char(
        string='Domain',
        help='Odoo domain to search recipients.'
    )

    notification_text = fields.Text(
        translate=True,
        required=True,
        help='Text of the notification'
    )

    buttons = fields.Many2many(
        'cdr.notification.button',
        help='Buttons that will be displayed on the alert to trigger certain actions'
    )

    active = fields.Boolean(
        default=True
    )

    event_raise = fields.Boolean(
        default=True
    )

    continue_raising = fields.Boolean(
        default=True
    )

    stop_raising = fields.Boolean()

    def get_domain(self):
        '''It is used as an evaluation alternative to parse the odoo domain defined
        string in the fields 'domain' or 'build_domain'

        '''
        domain = self.domain or self.build_domain
        try:
            if not domain or all(l.strip().startswith('#')
                                 for l in domain.splitlines()
                                 if l.strip()):
                domain = []
            elif any(l.strip().startswith('result')
                     for l in domain.splitlines()):
                domain = evaluate(domain, mode='exec', env=self.env, uid=self._uid)
            else:
                domain = evaluate(domain, env=self.env, uid=self._uid)
        except Exception:
            domain = []
        return domain

    @api.onchange('use_domain_builder')
    def onchange_use_domain_builder(self):
        '''If use_domain_builder changes an is True, parse the domain and save
        it as a string. If it is false it defaults the value of build_domain
        or  sets one by default.

        '''
        if self.use_domain_builder:
            domain = self.get_domain()
            domain = (str(domain) if domain else '')
            self.build_domain = domain
            self.domain = domain
        else:
            self.domain = (self.build_domain or '') + _('''
#  Odoo domain like: [('field_name', 'operator', value)]
#  or python code to return on result var a odoo domain like
#  if uid != 1:
#      result = [('id', '=', uid)]
#  else:
#      result = [('id', '!=', 1)]
#  env and uid are able to use.''')

    @api.onchange('build_domain')
    def onchange_build_domain(self):
        '''If the build_domain changes, it parses the domain-defined string
        and assigns it to field domain.

        '''
        if self.build_domain:
            domain = self.get_domain()
            domain = (str(domain) if domain else '')
            self.domain = domain

    @api.onchange('build_domain', 'domain')
    @api.depends('build_domain', 'domain')
    def get_recipients(self):
        '''Gets recipients that match a defined domain.

        '''
        for handler in self:
            domain = handler.get_domain()
            if domain:
                handler.recipients = self.env['res.users'].search(domain)
            else:
                handler.recipients = False

    @api.constrains('domain', 'build_domain')
    def _check_recipients(self):
        '''Restrict the use of at least one recipient.These recipients are the
        result of the defined domain.

        '''
        if not all(handler.recipients for handler in self):
            raise ValidationError(
                _('At least one recipient is necessary.'))

    @api.constrains('event_raise', 'continue_raising', 'stop_raising')
    def _check_signals(self):
        '''Check that there is at least some signal.

        '''
        if not all(h.event_raise or h.continue_raising or h.stop_raising
                   for h in self):
            raise ValidationError(_('At least one signal must be checked.'))

    def do_chat_notify(self):
        '''Notify by vigilant user by sending a message through the chat of odoo.

        '''
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
        '''Notifies all the recipients through the concept of channels of the
        odoo bus. Use the channels 'notify' and 'warn'.

        '''
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
                body=self.notification_text,
                type_notify=self.priority,
                actions=self.buttons.get_action())

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


class NotificationButton(models.Model):
    '''Represents the buttons that will be displayed in the alert to trigger
    actions.

    '''

    _name = 'cdr.notification.button'

    title = fields.Char(
        translate=True,
        required=True,
        help=''
    )

    action_id = fields.Char(
        help='Id of action'
    )

    action_dict = fields.Text(
        help='Action dict specification a python code that return a dict on result'
             ' variable'
    )

    @api.constrains('action_id', 'action_dict')
    def check_action(self):
        '''Verify that the action_id is a valid id of the ir.actions.actions
        model or a valid xml_id. Validates that the action_dict is correctly
        evaluated as a dictionary in python code.

        '''
        if not (self.action_id or self.action_dict):
            raise ValidationError(_('Action id or Action dict must be define.'))
        if self.action_id:
            try:
                action = self.env['ir.actions.actions'].browse(int(self.action_id))
                if not action.exists():
                    raise ValidationError('There is no action created with this action_id')
            except ValueError:
                try:
                    # Return the record corresponding to the given ``xml_id``
                    # in this case the xml_id is ``action_id``
                    action = self.env.ref(self.action_id)
                    action._name.startswith('ir.actions.')
                except Exception as e:
                    raise ValidationError(
                        'There is no action created with '
                        'this xml_id, remember the structure to invoke '
                        'it is addons.xml_id'
                    )
        if self.action_dict:
            try:
                evaluate(self.action_dict or 'result={}',
                         mode='exec', env=self.env)
            except Exception as e:
                raise ValidationError(e.message)

    def get_action(self):
        '''If action id is defined corresponding openerp action will be update
        with action dict and executed, else action dict must be a valid openerp
        action dict.

        '''
        result = []
        for item in self:
            res = dict(title=item.title)
            if item.action_id:
                res.update(action_id=item.action_id)
            if item.action_dict:
                res.update(evaluate(item.action_dict or 'result={}',
                                    mode='exec', env=self.env))
            result.append(res)
        return result
