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
        self.mail_message = self.env['mail.message']
        self.A = partner.create({'name': 'A'})
        self.B = partner.create({'name': 'B'})

    def test_check_informal_reference(self):
        self.objectmerger._check_informal_reference(self.B, self.A)
        m = self.mail_message.search([('res_id', '=', self.B.id)])
        self.assertFalse(m)
