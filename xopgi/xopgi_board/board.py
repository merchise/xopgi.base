# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.board
# ---------------------------------------------------------------------
# Copyright (c) 2015-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2015-10-29

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from itertools import groupby

from xoeuf import api, models
from xoeuf.odoo import _

import logging
logger = logging.getLogger(__name__)
del logging


def lineal_color_scaling(value,  # 0-1 float
                         start_point=(255, 0, 0),  # red
                         end_point=(0, 255, 0)):  # green
    from colorsys import rgb_to_hsv, hsv_to_rgb as _hsv_to_rgb
    start_point = rgb_to_hsv(*start_point)
    end_point = rgb_to_hsv(*end_point)

    def hsv_to_rgb(*a):
        res = _hsv_to_rgb(*a)
        return tuple(int(x) for x in res)

    def transition(value, start_point, end_point):
        return start_point + (end_point - start_point) * value

    def transition3(value, (s1, s2, s3), (e1, e2, e3)):
        r1 = transition(value, s1, e1)
        r2 = transition(value, s2, e2)
        r3 = transition(value, s3, e3)
        return (r1, r2, r3)

    return hsv_to_rgb(*transition3(value, start_point, end_point))


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
    value = value or 0.0
    sector = 11
    if target:
        if target >= value:
            sector = 1.0 if inverted else float(value) / target
        else:
            sector = 0.0 if inverted else 1.0
    if sector > 1.0:
        color = '#e2e2e0'
    else:
        color = 'rgb(%s, %s, %s)' % lineal_color_scaling(sector)
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
