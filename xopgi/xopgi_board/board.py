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

from itertools import groupby

from xoeuf import api, models
from xoeuf.odoo import _

import logging
logger = logging.getLogger(__name__)
del logging


def get_query_from_domain(self, domain):
    query = self._where_calc(domain)
    self._apply_ir_rules(query, 'read')
    from_clause, where_clause, where_params = query.get_sql()
    where_str = where_clause and (" WHERE %s" % where_clause) or ''
    return from_clause, where_str, where_params


def get_targets(self, values, indicators=(), from_company=False,
                inverted=False):
    target_obj = self.env.user.company_id if from_company else self.env.user
    for indicator in indicators:
        target = getattr(target_obj, 'target_%s' % indicator, 0)
        values[indicator].update(
            target=target,
            color=get_indicator_color(target, values[indicator]['this_month'],
                                      inverted=inverted)
        )


def get_indicator_color(target, value, inverted=False):
    '''Return the name of CSS class which indicates the compliance of `value`
    over target.

    If the value of the indicator is less than zero, the color will be gray.

    If the indicator is inverted the color scale is inverted. This means that
    if its value increases your result will be worse. We subtract the
    compliance from 1 to use the same scale to assign the colors and reverse
    their result.

    Compliance is given by the ratio `value/target`:

    - 0%- 49,9..% is red
    - 50%-99,9..% is orange
    - 100% or greater- is green

    '''
    value = value or 0.0
    color = 'xb_lightgray_bg'
    if target and target > 0 and value >= 0:
        compliance = 1 if value > target else float(value) / target
        if inverted:
            compliance = 1 - compliance
        if 0 <= compliance < 0.5:
            color = 'xb_red_bg'
        elif 0.5 <= compliance < 1:
            color = 'xb_orange_bg'
        elif compliance >= 1:
            color = 'xb_green_bg'
    return color


class XopgiBoard(models.Model):
    _name = 'xopgi.board'
    _description = "Board"

    @api.model
    def get_board_widgets(self):
        '''Gets data from all widgets and groups them by category

        '''
        logger.debug(
            'Starting search widgets for user: %s' % self.env.user.login)
        lst = self.get_data()
        result = [list(itr) for k, itr in
                  groupby(lst, lambda x: x.get('category', x) or x)]
        return result

    def get_data(self):
        '''Gets the data of all the widgets the user has access to.

        '''
        return self.env['xopgi.board.widget'].get_widgets_dict()

    @api.model
    def modify_target_dashboard(self, target_name, target_value,
                                mode='individual'):
        target_obj = (self.env.user.company_id.sudo()
                      if mode == 'company'
                      else self.env.user.sudo())
        target_value = int(target_value) if target_value else 0
        target_name = target_name.split('-', 1)[-1]
        if hasattr(target_obj, 'target_' + target_name):
            return setattr(target_obj, 'target_' + target_name, target_value)

    @api.multi
    def name_get(self):
        return [(i.id, _('Preview')) for i in self]
