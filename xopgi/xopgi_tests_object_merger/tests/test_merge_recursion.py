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


class TestObjectRecursion(TransactionCase):
    def setUp(self):
        super(TestObjectRecursion, self).setUp()
        self.objectmerger = self.env['object.merger']
        Model_a = self.env['model.a']
        self.B = Model_a.create({'add_char': 'B'})
        self.C = Model_a.create({'add_char': 'C', 'parent_id': self.B.id})
        self.A = Model_a.create({'add_char': 'A', 'parent_id': self.C.id})

    def test_merger_recursion(self):
        self.objectmerger.merge(self.B, self.A)
        self.assertFalse(self.A.parent_id)
