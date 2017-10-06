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
        self.irmodel = self.env['ir.model']
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

    def test_merger_partner(self):
        partner = self.partner.search(['parent_id', '=', self.sources.id])
        self.objectmerger.merge(self.sources, self.target)
        self.assertFalse(self.sources.active)
        self.assertEqual(
            self.target.mobile,
            (self.target.mobile + self.sources.mobile))
        if self.irmodel.merge_cyclic:
            self.assertEqual(partner.parent_id.id, self.target.id)
