#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

'''Differentiate the date for currency rating computation.

Odoo normally uses today or the key 'date' in the context to compute the
currency rates.  However, this key is also used in other places for other
purposes (pricelist selection, etc).

We create the 'currency_rating_date' key in the context to force a different
date for currency rate computations.  You may pass either a datetime, a date,
or a string (as Odoo requires).

'''

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoeuf import api, models


class CurrencyRateDate(models.Model):
    _inherit = 'res.currency'

    @api.multi
    def _compute_current_rate(self):
        from xoutil.symbols import Unset
        from xoeuf.tools import dt2str
        rating_date = self._context.get('currency_rating_date', Unset)
        if rating_date is not Unset:
            # Ensure an Odoo-friendly string, this will allow clients to pass
            # dates/datetime and keep them away from the 'date str' mess.
            rating_date = dt2str(rating_date)
            new_self = self.with_context(date=rating_date)
        else:
            new_self = self
        super(CurrencyRateDate, self)._compute_current_rate()
        if new_self is not self:
            # I have to copy the rate from one context to another (they don't
            # share the cache where the rate is put).
            #
            # TODO: Port this to a general tool: You need to call super with a
            # different context, but to copy the cache from the new 'self' to
            # the actual one.
            #
            # A word of WARNING:  Odoo does not share the cache for good
            # reasons:  In this case, the res_currency model is programmed to
            # have a rate a given 'date'.  Which means that if the context
            # context changes, the rate changes accordingly.  In our case, if
            # the context has 'currency_rating_date' it will trump over the
            # 'date', nothing more.
            for currency in self:
                new_self_currency = new_self.browse(currency.id)
                currency.rate = new_self_currency.rate
