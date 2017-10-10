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
    partner_id = fields.Many2one('res.partner', 'Contact')


class InformalReference(models.Model):
    _name = 'test.merger.reference'

    subject = fields.Char()
    body = fields.Text()
    res_id = fields.Integer()
