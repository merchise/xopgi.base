#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# handler_v8
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


from xoeuf import MAJOR_ODOO_VERSION
from xoeuf import api, models


assert MAJOR_ODOO_VERSION == 8, 'This module only works for Odoo 8'


class EventHandler(models.Model):
    _inherit = 'cdr.event.basic.handler'

    @api.requires_singleton
    def do_chat_notify(self):
        '''Make the vigilant send a chat message.

        '''
        from xoeuf.osv.orm import REPLACEWITH_RELATED
        vigilant = self.env.ref('xopgi_cdr_notification.vigilant_user')
        session_ids = self.env['im_chat.session'].search(
            [('user_ids', '=', vigilant.id)]
        )
        for recipient in self.recipients:
            # override self to get recipient right lang translation
            self = self.with_context(lang=recipient.lang)
            session_id = session_ids.filtered(
                lambda s: recipient in s.user_ids and len(s.user_ids) == 2
            )
            if not session_id:
                session_id = self.env['im_chat.session'].create(dict(
                    user_ids=[REPLACEWITH_RELATED(recipient.id, vigilant.id)]
                ))
            notification_text = self.prioritized_notification_text
            self.env['im_chat.message'].post(
                vigilant.id, session_id[0].uuid,
                'meta', notification_text
            )
