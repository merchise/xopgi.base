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


class TestObjectMerger(TransactionCase):
    def setUp(self):
        super(TestObjectMerger, self).setUp()
        self.objectmerger = self.env['object.merger']
        Partner = self.env['res.partner']
        Test_fks = self.env['test.merger.fks']
        Test_settings = self.env['test.merger.settings']
        self.ir_model_fields = self.env['ir.model.fields']
        self.irmodel = self.env['ir.model'].search([('model', '=', 'res.partner')])
        self.field = self.env['field.merge.way']
        self.settings = self.env['test.merger.settings']
        self.target = Partner.create({'name': 'Etecsa',
                                      'email': 'etecsa@email.cu',
                                      'mobile': '523478'})
        self.sources = Partner.create({'name': 'Copextel',
                                       'email': 'Copextel@email.cu',
                                       'mobile': '00000'})
        self.parent_id = Partner.create({'name': 'Copextel División Pinar',
                                         'email': 'Copextelpinar@email.cu',
                                         'mobile': '048766229',
                                         'parent_id': self.sources.id})
        self.partner_idfk = Test_fks.create({'name': 'Venta de laptop',
                                             'description': 'Venta',
                                             'partner_id': self.sources.id})
        self.settings1 = Test_settings.create({'add_char': 'Venta',
                                              'add_text': 'Venta de laptop',
                                              'price_int': 10,
                                              'cost_float': 12.3})
        self.settings2 = Test_settings.create({'add_char': 'Compra',
                                               'add_text': 'Compra de PC',
                                               'price_int': 20,
                                               'cost_float': 7.3})
        self.irmodel.write({'merge_cyclic': True})

    def test_merger_partner(self):
        self.objectmerger.merge(self.sources, self.target)
        self.assertFalse(self.sources.active)
        self.assertEqual((self.parent_id.parent_id.id), self.target.id)
        self.assertEqual((self.partner_idfk.partner_id.id), self.target.id)

    def test_add_fields(self):
        field = self.ir_model_fields.search([('name', '=', 'add_char'),
                                             ('model', '=', 'test.merger.settings')])
        result = self.field.apply_add(self.settings2, self.settings1, field)
        self.assertEqual((self.settings1.add_char + ' ' + self.settings2.add_char), result)

    def test_sum_fields(self):
        field = self.ir_model_fields.search([('name', '=', 'price_int'),
                                             ('model', '=', 'test.merger.settings')])
        result = self.field.apply_sum(self.settings2, self.settings1, field)
        self.assertEqual((self.settings2.price_int + self.settings1.price_int), result)
        field = self.ir_model_fields.search([('name', '=', 'cost_float'),
                                             ('model', '=', 'test.merger.settings')])
        result = self.field.apply_sum(self.settings2, self.settings1, field)
        self.assertEqual((self.settings2.cost_float + self.settings1.cost_float), result)

    def test_max_fields(self):
        field = self.ir_model_fields.search([('name', '=', 'price_int'),
                                             ('model', '=', 'test.merger.settings')])
        result = self.field.apply_max(self.settings2, self.settings1, field)
        self.assertGreater(result, self.settings1.price_int)

    def test_min_fields(self):
        field = self.ir_model_fields.search([('name', '=', 'cost_float'),
                                             ('model', '=', 'test.merger.settings')])
        result = self.field.apply_min(self.settings2, self.settings1, field)
        self.assertGreater(self.settings1.cost_float, result)
