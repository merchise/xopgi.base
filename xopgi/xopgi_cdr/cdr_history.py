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

from xoeuf.odoo import fields, models


class CDRHistory(models.Model):
    '''History of control variable, evidences and your values in evaluation cycles.

    '''
    _name = 'cdr.history'
    _inherit = ['cdr.value']
    _order = 'cycle desc'

    identifier = fields.Many2one(
        'cdr.identifier',
        required=True,
        ondelete='cascade',
    )

    cycle = fields.Many2one(
        'cdr.evaluation.cycle',
        required=True,
        ondelete='cascade',
    )
