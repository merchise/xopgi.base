# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr.cdr_history
# ---------------------------------------------------------------------
# Copyright (c) 2016 Merchise Autrement and Contributors
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

from openerp import fields, models


class CDRHistory(models.Model):
    _name = 'cdr.history'

    _order = 'cycle desc'

    identifier = fields.Many2one('cdr.identifier', required=True,
                                 ondelete='cascade')
    cycle = fields.Many2one('cdr.evaluation.cycle', required=True)
    value = fields.Char()
