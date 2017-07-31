# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr.cdr_history
# ---------------------------------------------------------------------
# Copyright (c) 2016-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-02-13

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoeuf.odoo import fields, models


class CDRHistory(models.Model):
    '''History of control variable, evidences and your values in evaluation cycles.

    '''
    _name = 'cdr.history'

    _order = 'cycle desc'

    identifier = fields.Many2one(
        'cdr.identifier',
        required=True,
        ondelete='cascade',
        help='Available python identifier. This can be a variable or evidences '
    )

    cycle = fields.Many2one(
        'cdr.evaluation.cycle',
        required=True,
        help='<CDR_evaluation_cycle>'
    )

    value = fields.Char(
        help='Value of the evaluation'
    )
