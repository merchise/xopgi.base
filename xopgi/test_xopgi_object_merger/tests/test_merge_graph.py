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

from xoeuf.odoo.exceptions import ValidationError
from xoeuf.odoo.tests.common import TransactionCase


class TestMerge(TransactionCase):
    def setUp(self):
        super(TestMerge, self).setUp()
        self.objectmerger = self.env['object.merger']
        partner = self.env['res.partner']
        self.partner_A = partner.create({'name': 'A'})
        self.partner_B = partner.create({'name': 'B', 'parent_id': self.partner_A.id})
        self.partner_C = partner.create({'name': 'C', 'parent_id': self.partner_B.id})

    def test_merge_a_and_c_targeting_c(self):
        with self.assertRaises(ValidationError):
            self.objectmerger.merge(self.partner_A, self.partner_C)

    def test_merge_a_and_c_targeting_a(self):
        # Notice merge does not commute.
        self.objectmerger.merge(self.partner_C, self.partner_A)
        self.assertEqual(self.partner_B.parent_id, self.partner_A)
        self.assertNotEqual(self.partner_A.parent_id, self.partner_B)
