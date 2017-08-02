#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# identifiers
# ---------------------------------------------------------------------
# Copyright (c) 2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2017-08-01


from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoeuf import models, fields, api
from xoeuf.odoo import _
from xoeuf.odoo.exceptions import ValidationError


def check_identifier(identifier):
    """ Check identifier is a correct python identifier and not shadow a
    global builtin.

    """
    if not identifier[0].isalpha() and identifier[0] != '_':
        return False
    if identifier in globals().get('__builtins__', {}):
        return False
    if len(identifier) > 1:
        for char in identifier[1:]:
            if not char.isalnum() and char != '_':
                return False
    return True


class CDRIdentifier(models.Model):
    _name = 'cdr.identifier'
    _inherit = ['cdr.value']

    name = fields.Char(
        required=True,
        help="Must be a available python identifier.\n"
             "Just letters, digit (never in first position) "
             "and underscore are allowed."
    )

    evaluations = fields.One2many(
        'cdr.history',
        'identifier'
    )
    _sql_constraints = [
        ('identifier_name_unique', 'unique(name)', 'Name already exists')
    ]

    @api.constrains('name')
    def check_name(self):
        '''Check name of a CDRIdentifier

        '''
        if not check_identifier(self.name):
            raise ValidationError(
                _("Name must be a available python identifier")
            )
