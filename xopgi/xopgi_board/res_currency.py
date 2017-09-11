# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.res_currency
# ---------------------------------------------------------------------
# Copyright (c) 2015-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

import json
from xoeuf import api, models


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def get_format_currencies_js_function(self, return_type='float'):
        '''Extend original function to allow return an integer value

        '''
        format_number_str = "openerp.web.format_value(" \
                            "arguments[0], {type: 'integer'}, 0)"
        if return_type == 'float':
            function = super(ResCurrency, self).get_format_currencies_js_function()
        else:
            function = ""
            for row in self.search_read(
                    domain=[],
                    fields=['id', 'name', 'symbol', 'position']):
                symbol = row['symbol'] or row['name']
                if row['position'] == 'after':
                    return_str = "return {value} + '\\xA0' + {symbol};"
                else:
                    return_str = "return {symbol} + '\\xA0' + {value};"
                function += "if (arguments[1] === %s) { %s }" % (
                    str(row['id']), return_str.format(
                        symbol=json.dumps(symbol), value=format_number_str))
        return function + 'return {value};'.format(value=format_number_str)
