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


class TestObjectMerger(TransactionCase):
    def setUp(self):
        super(TestObjectMerger, self).setUp()
        self.objectmerger = self.env['object.merger']
        Model_a = self.env['model.a']
        Model_b = self.env['model.b']
        self.ir_model_fields = self.env['ir.model.fields']
        self.irmodel = self.env['ir.model'].search([('model', '=', 'model.a')])
        self.field = self.env['field.merge.way.rel']
        self.target = Model_a.create({'add_char': 'Etecsa',
                                      'add_text': 'Empresa telecomunicaciones',
                                      'price_int': 20,
                                      'cost_float': 7.4,
                                      'min_int': 2,
                                      'max_int': 9})
        self.sources = Model_a.create({'add_char': 'Copextel',
                                       'add_text': 'Empresa TV Panda',
                                       'price_int': 100,
                                       'cost_float': 20.4,
                                       'min_int': 4,
                                       'max_int': 12})
        self.parent_id = Model_a.create({'add_char': 'Copextel Pinar',
                                         'add_text': 'Empresa TV Panda Pinar',
                                         'price_int': 200,
                                         'cost_float': 20.4,
                                         'min_int': 6,
                                         'max_int': 15,
                                         'parent_id': self.sources.id})
        self.modela_id = Model_b.create({'name': 'Venta de Laptop',
                                         'modela_id': self.sources.id})
        self.sources.meldb_ids += Model_a.meldb_ids.create({'name': 'Venta de PC'})

        field_char = self.ir_model_fields.search([('name', '=', 'add_char'),
                                                  ('model', '=', 'model.a')])
        field_text = self.ir_model_fields.search([('name', '=', 'add_text'),
                                                  ('model', '=', 'model.a')])
        field_int = self.ir_model_fields.search([('name', '=', 'price_int'),
                                                 ('model', '=', 'model.a')])
        field_float = self.ir_model_fields.search([('name', '=', 'cost_float'),
                                                   ('model', '=', 'model.a')])
        field_min_int = self.ir_model_fields.search([('name', '=', 'min_int'),
                                                     ('model', '=', 'model.a')])
        field_max_int = self.ir_model_fields.search([('name', '=', 'max_int'),
                                                     ('model', '=', 'model.a')])

        addid = self.env.ref('xopgi_object_merger.add').id
        sumid = self.env.ref('xopgi_object_merger.sum').id
        maxid = self.env.ref('xopgi_object_merger.max').id
        minid = self.env.ref('xopgi_object_merger.min').id

        self.field.create(dict(name=field_char.id, merge_way=addid, model=self.irmodel.id))
        self.field.create(dict(name=field_text.id, merge_way=addid, model=self.irmodel.id))
        self.field.create(dict(name=field_int.id, merge_way=sumid, model=self.irmodel.id))
        self.field.create(dict(name=field_float.id, merge_way=sumid, model=self.irmodel.id))
        self.field.create(dict(name=field_max_int.id, merge_way=maxid, model=self.irmodel.id))
        self.field.create(dict(name=field_min_int.id, merge_way=minid, model=self.irmodel.id))

    def test_merger(self):
        result_char = self.target.add_char + ' ' + self.sources.add_char
        result_text = self.target.add_text + ' ' + self.sources.add_text
        result_sum = self.target.price_int + self.sources.price_int
        result_sum_float = round((self.target.cost_float +
                                  self.sources.cost_float), 1)
        self.objectmerger.merge(self.sources, self.target)
        self.assertFalse(self.sources.active)
        self.assertEqual(result_char, self.target.add_char)
        self.assertEqual(result_text, self.target.add_text)
        self.assertEqual(self.target.price_int, result_sum)
        self.assertEqual(result_sum_float, self.target.cost_float)
        self.assertEqual(self.target.min_int, 2)
        self.assertEqual(self.target.max_int, 12)
        self.assertEqual(self.modela_id.modela_id, self.target)
        self.assertEqual(self.target.meldb_ids.melda_ids, self.target)
