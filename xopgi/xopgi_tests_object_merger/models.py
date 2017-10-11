#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# test_module
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


from xoeuf import models, fields


class Checkfks(models.Model):
    _name = 'test.merger.fks'

    name = fields.Char()
    description = fields.Text()
    merger_id = fields.Many2one('test.merger.settings', 'Merge')


class Test_merger_settings(models.Model):
    _name = 'test.merger.settings'

    add_char = fields.Char()
    add_text = fields.Text()
    price_int = fields.Integer()
    cost_float = fields.Float()
    parent_id = fields.Many2one('test.merger.settings', 'Parent')


class Test_many2many(models.Model):
    _name = 'test.many2many'

    name = fields.Char()
    merge_settings_ids = fields.Many2many(
        'test.merger.settings',
        'test_many2many_merger_settings_rel',
        'many2many_id',
        'merger_id',
        'Test_many2many'
    )


class Test_inherit(models.Model):
    _inherit = 'test.merger.settigs'

    name = fields.Char()


class Test_reference(models.Model):
    _name = 'test.reference'

    name = fields.Char()
    model = fields.Char()
    res_id = fields.Integer()
