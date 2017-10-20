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
        self.A = partner.create({'name': 'A'})
        self.B = partner.create({'name': 'B', 'parent_id': self.A.id})
        self.C = partner.create({'name': 'C', 'parent_id': self.B.id})

    def test_merge_a_and_c_targeting_c(self):
        with self.assertRaises(ValidationError):
            self.objectmerger.merge(self.A, self.C)

    def test_merge_a_and_c_targeting_a(self):
        self.objectmerger.merge(self.C, self.A)
        self.assertEqual(self.D.partner_id, self.A)
        self.assertEqual(self.A.category_id.partner_ids, self.A)
        self.assertEqual(self.B.parent_id, self.A)
        self.assertNotEqual(self.A.parent_id, self.B)
