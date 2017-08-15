#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# handler_v9
# ---------------------------------------------------------------------
# Copyright (c) 2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2017-07-17


from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoeuf import api, models
from xoeuf.models.proxy import MailChannel

from xoeuf import MAJOR_ODOO_VERSION
assert MAJOR_ODOO_VERSION in (9, 10), 'This module only works for Odoo 9, 10'


class EventHandler(models.Model):
    _inherit = 'cdr.event.basic.handler'

    @api.requires_singleton
    def do_chat_notify(self):
        '''Make the vigilant send a chat message.

        '''
        vigilant = self.env.ref('xopgi_cdr_notification.vigilant_user')
        Vigilant = MailChannel.sudo(vigilant.id)
        vigilant_partner = vigilant.partner_id.id
        for recipient in self.recipients:
            recipient_partner = recipient.partner_id.id
            channel_info = Vigilant.channel_get(
                [recipient_partner]
            )
            if channel_info:
                channel = Vigilant.browse(channel_info['id'])
                notification_text = self.prioritized_notification_text
                channel.message_post(
                    body=notification_text,
                    message_type="comment",
                    subtype="mail.mt_comment",
                    author_id=vigilant_partner
                )
