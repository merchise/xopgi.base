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


class TestObjectmailalias(TransactionCase):
    def setUp(self):
        super(TestObjectmailalias, self).setUp()
        self.objectmerger = self.env['object.merger']
        partner = self.env['res.partner']
        mail_alias = self.env['mail.alias']
        self.mail_alias = self.env['mail.alias']
        self.H = partner.create({'name': 'H'})
        self.G = partner.create({'name': 'G'})
        res_partner = self.env['ir.model'].search(
            [('model', '=', 'res.partner')])
        category_id = partner.category_id.create(dict(name='Category'))
        self.G.category_id += category_id
        self.alias1 = mail_alias.create(
            dict(alias_model_id=res_partner.id,
                 alias_defaults={'type': 'out_invoice',
                                 'parent_id': self.G.id, 'currency_id': 1}))
        self.alias2 = mail_alias.create(
            dict(alias_model_id=res_partner.id,
                 alias_defaults={'type': 'out_invoice',
                                 'message_follower_ids': [(category_id.id, self.G.id)],
                                 'currency_id': 1}))

    def test_check_mail_alias(self):
        self.objectmerger._check_on_alias_defaults(self.G, self.H)
        alias1 = self.alias1.alias_defaults
        val = eval(alias1)
        id = val['parent_id']
        self.assertEqual(self.H.id, id)
        alias2 = self.alias2.alias_defaults
        val = eval(alias2)
        id = val['message_follower_ids'][-1][-1]
        self.assertEqual(self.H.id, id)
