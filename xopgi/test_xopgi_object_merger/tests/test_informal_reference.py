#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoeuf.odoo.tests.common import TransactionCase


class TestObjectinformalRef(TransactionCase):
    def setUp(self):
        super(TestObjectinformalRef, self).setUp()
        self.objectmerger = self.env['object.merger']
        partner = self.env['res.partner']
        self.Message = self.env['mail.message']
        self.partner_A = partner.create({'name': 'A'})
        self.partner_B = partner.create({'name': 'B'})
        # Ensure partner B has at least a message
        self.partner_B.message_post()

    def test_mail_messages_are_moved(self):
        # The thread of a message is represented as an 'informal reference',
        # so we're testing that the merge procedure do merge those.
        partner_a_messages = self.Message.search(
            [('res_id', '=', self.partner_A.id)],
            count=True
        )
        partner_b_messages = self.Message.search(
            [('res_id', '=', self.partner_B.id)],
            count=True
        )
        B = self.partner_B.id
        self.objectmerger.merge(self.partner_B, self.partner_A)
        self.Message.invalidate_cache()
        self.assertEqual(
            self.Message.search(
                [('res_id', '=', B)],
                count=True
            ),
            0
        )
        merged_messages = self.Message.search(
            [('res_id', '=', self.partner_A.id)],
            count=True
        )
        self.assertEqual(
            merged_messages,
            partner_a_messages + partner_b_messages
        )
        self.assertGreater(merged_messages, 0)
