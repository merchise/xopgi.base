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


from xoeuf import models, fields


class B(models.Model):
    _name = 'model.b'

    name = fields.Char()
    modela_id = fields.Many2one('model.a', 'Merge')
    melda_ids = fields.Many2many(comodel_name='model.a',
                                 column1='meld_column1_id',
                                 column2='meld_column2_id',
                                 string='relation')
    partner_id = fields.Many2one('res.partner', 'Parent')


class A(models.Model):
    _name = 'model.a'

    add_char = fields.Char()
    add_text = fields.Text()
    price_int = fields.Integer()
    cost_float = fields.Float()
    min_int = fields.Integer()
    max_int = fields.Integer()
    active = fields.Boolean(default=True)
    parent_id = fields.Many2one('model.a', 'Parent')
    meldb_ids = fields.Many2many(comodel_name='model.b',
                                 column1='meld_column2_id',
                                 column2='meld_column1_id',
                                 string='relation')
