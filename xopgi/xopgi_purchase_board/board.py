# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_purchase_board.board.py
# ---------------------------------------------------------------------
# Copyright (c) 2013-2015 Merchise Autrement
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-11-17

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from openerp import api, models, _
from openerp.addons.xopgi_board.board import lineal_color_scaling, \
    get_query_from_domain, get_targets
from xoeuf.tools import dt2str, date2str
from xoutil import logger


class PurchaseBoard(models.AbstractModel):
    _name = 'purchase.board'

    @api.model
    def get_data(self, today, mode=None):
        res = {
            'mode': mode or '',
            'program': {'today': 0, 'overdue': 0},
            'coord_dossier': {'today': 0, 'overdue': 0, 'next_7_days': 0},
            'confirm_order': {'today': 0, 'overdue': 0, 'next_7_days': 0},
            'not_invoiced': {'today': 0, 'overdue': 0, 'next_7_days': 0},
            'reserve_send_time': {
                'this_month': 0, 'last_month': 0, 'color': 0},
            'supplier_response_time': {
                'this_month': 0, 'last_month': 0, 'color': 0},
            'purchase_time': {
                'this_month': 0, 'last_month': 0, 'color': 0},
        }
        first_month_day = today.replace(day=1)
        first_last_month_day = dt2str(first_month_day - relativedelta(
            months=+1))
        first_month_day = dt2str(first_month_day)
        next_22_days = dt2str(today + timedelta(days=22))
        next_31_days = dt2str(today + timedelta(days=31))
        last_week = dt2str(today + timedelta(days=-7))
        next_8_days = dt2str(today + timedelta(days=8))
        today = dt2str(today)
        coord_board_obj = self.env['coordination.board.util']
        #  Purchase Programs
        logger.debug('Starting to search programs purchase')
        res['program'].update(coord_board_obj._get_purchase_programs(
            mode == 'company', last_week))
        #  Dossier to coordinate
        logger.debug('Starting to search dossier to coordinate')
        res['coord_dossier'].update(coord_board_obj._get_coord_dossiers(
            mode == 'company', today, next_22_days, next_31_days))
        #  Quotations to coordinate and not invoiced
        temp = self._get_purchase_orders(
            mode == 'company', today, next_8_days, next_22_days, next_31_days)
        for column in ['confirm_order', 'not_invoiced']:
            res[column].update(temp.get(column, {}))
        #  Indicators
        indicators = ['reserve_send_time', 'supplier_response_time',
                      'purchase_time']
        logger.debug('Starting to search indicators')
        temp = coord_board_obj._get_indicators(
            mode == 'company', first_month_day, first_last_month_day,
            indicators)
        for indicator in indicators:
            res[indicator].update(temp.get(indicator, {}))
        # targets
        logger.debug('Getting targets')
        get_targets(self, res, indicators, mode == 'company')
        return res

    def _get_purchase_orders(self, base_domain, today, next_8_days,
                             next_22_days, next_31_days):
        query = """
        SELECT
          SUM(CASE WHEN minimum_planned_date >= %%s and
              minimum_planned_date < %%s
              THEN 1 ELSE 0 END) AS today,
          SUM(CASE WHEN %%s <= minimum_planned_date
              THEN 1 ELSE 0 END) AS next_7_days,
          SUM(CASE WHEN minimum_planned_date < %%s
              THEN 1 ELSE 0 END) AS overdue
        FROM
          %s
        %s
        """
        domain = ([] if base_domain else [('user_id', '=', self._uid)]) + [
            ('state', '!=', 'cancel'),
            ('minimum_planned_date', '!=', False),
            ('minimum_planned_date', '>=', today),
            ('minimum_planned_date', '<', next_31_days)]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['purchase.order'], domain)
        query_args = (next_8_days, next_22_days, next_8_days,
                      next_8_days) + tuple(
            where_params)
        self._cr.execute(query % (from_clause, where_str), query_args)
        data = {'confirm_order': self._cr.dictfetchone() or {}}
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['purchase.order'], domain + [('open', '=', True)])
        query_args = (next_8_days, next_22_days, next_8_days, next_8_days) + tuple(
            where_params)
        self._cr.execute(query % (from_clause, where_str), query_args)
        data['not_invoiced'] = self._cr.dictfetchone() or {}
        return data

