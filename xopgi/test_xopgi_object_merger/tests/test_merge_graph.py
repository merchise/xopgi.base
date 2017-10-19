#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# test_object_merger
# ---------------------------------------------------------------------
# Copyright (c) 2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2017-09-20

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoeuf.odoo.tests.common import TransactionCase


class TestMerge(TransactionCase):
    def setUp(self):
        super(TestMerge, self).setUp()
        self.objectmerger = self.env['object.merger']
        partner = self.env['res.partner']
        modelb = self.env['model.b']
        self.A = partner.create({'name': 'A'})
        self.B = partner.create({'name': 'B', 'parent_id': self.A.id})
        self.C = partner.create({'name': 'C', 'parent_id': self.B.id})
        self.D = modelb.create(dict(name='MA', partner_id=self.A.id))
        categoryb = partner.category_id.create(dict(name='CategoryB'))
        self.C.category_id += categoryb

    def test_merge_a_and_c_targeting_c(self):
        self.objectmerger.merge(self.A, self.C)
        self.assertEqual(self.D.partner_id, self.C)
        self.assertEqual(self.C.category_id.partner_ids, self.C)
        self.assertEqual(self.B.parent_id, self.C)
        self.assertEqual(self.C.parent_id, self.B)

    def test_merge_a_and_c_targeting_a(self):
        self.objectmerger.merge(self.C, self.A)
        self.assertEqual(self.D.partner_id, self.A)
        self.assertEqual(self.A.category_id.partner_ids, self.A)
        self.assertEqual(self.B.parent_id, self.A)
        self.assertFalse(self.A.parent_id, self.B)
