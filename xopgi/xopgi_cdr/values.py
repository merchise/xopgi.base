#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# base
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


from xoeuf import fields, models, api
from xoeuf.odoo.tools.safe_eval import safe_eval


class Value(models.AbstractModel):
    '''A variant value mixin.

    Contains a single value that it represented a VARCHAR to the DB but is a
    Python object.

    Any object whose `repr()` result is sensible can be stored/retrieved.

    Provides `value`:attr: with the repr'ed representation and `result`:attr:
    with the Python object.

    '''
    _name = 'cdr.value'

    value = fields.Char(
        # This stores the representation (result of repr) of the value.  You
        # may use `result` to read/update this field.  If you use Odoo's
        # write/create, or set this field directly you MUST ensure to pass the
        # result of `repr()`.  The `write/create` methods below ensure the
        # writing to 'result' works.
        help='Value of the evaluation'
    )

    @api.multi
    def write(self, values):
        # Makes writing to 'result' work.  If you pass both 'value' and
        # 'result', 'result' wins.
        if 'result' in values:
            values['value'] = repr(values.pop('result'))
        return super(Value, self).write(values)

    @api.model
    def create(self, values):
        # Makes writing to 'result' work.  If you pass both 'value' and
        # 'result', 'result' wins.
        if 'result' in values:
            values['value'] = repr(values.pop('result'))
        return super(Value, self).create(values)

    def _get_result(self):
        return safe_eval(self.value) if self.value else self.value

    def _set_result(self, value):
        self.value = repr(value)

    def _del_result(self):
        self.value = None

    result = fields.Property(
        getter=_get_result,
        setter=_set_result,
        deleter=_del_result,
    )
    del _get_result, _set_result, _del_result
