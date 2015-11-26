# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_coordination_board.board.py
# ---------------------------------------------------------------------
# Copyright (c) 2013-2015 Merchise Autrement
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-11-14

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, _
from openerp.addons.xopgi_board.board import lineal_color_scaling, \
    get_query_from_domain, get_targets
from xoeuf.tools import dt2str, date2str
from xoutil import logger


INDICATORS = ['planification_time', 'reserve_send_time',
              'supplier_response_time', 'purchase_time']


class CoordinationBoardUtil(models.AbstractModel):
    _name = 'coordination.board.util'

    @api.model
    def get_data(self, mode=None):
        res = {
            'mode': mode or '',
            'quotation': {'today': 0, 'overdue': 0},
            'program': {'today': 0, 'overdue': 0},
            'coord_dossier': {'today': 0, 'overdue': 0, 'next_7_days': 0},
            'close_dossier': {'today': 0, 'overdue': 0, 'next_7_days': 0},
            'planification_time': {'this_month': 0, 'last_month': 0, 'color': 0},
            'reserve_send_time': {
                'this_month': 0, 'last_month': 0, 'color': 0},
            'supplier_response_time': {
                'this_month': 0, 'last_month': 0, 'color': 0},
            'purchase_time': {
                'this_month': 0, 'last_month': 0, 'color': 0},
        }
        today = date.today()
        first_month_day = today.replace(day=1)
        first_last_month_day = first_month_day - relativedelta(months=+1)
        next_21_days = today + timedelta(days=21)
        next_30_days = today + timedelta(days=30)
        last_week = today + timedelta(days=-7)
        last2_week = today + timedelta(days=-15)
        # Quotations to confirm
        logger.debug('Starting to search quotations to confirm')
        res['quotation'].update(
            self._get_quotations(mode == 'company', last_week))
        # Purchase Programs
        logger.debug('Starting to search programs purchase')
        res['program'].update(
            self._get_purchase_programs(mode == 'company', last_week))
        # Dossier to coordinate
        logger.debug('Starting to search dossier to coordinate')
        res['coord_dossier'].update(
            self._get_coord_dossiers(mode == 'company', today,
                                     next_21_days, next_30_days))
        # Dossier to close
        logger.debug('Starting to search dossiers to close')
        res['close_dossier'].update(self._get_close_dossier(
            mode == 'company', today, last_week, last2_week))
        #indicadores
        logger.debug('Starting to search indicators')
        temp = self._get_indicators(mode == 'company', first_month_day,
                                    first_last_month_day, INDICATORS)
        for indicator in INDICATORS:
            res[indicator].update(temp.get(indicator, {}))
        # targets
        logger.debug('Getting targets')
        get_targets(self, res, INDICATORS, mode == 'company')
        return res

    def _get_quotations(self, base_domain, last_week):
        base_domain = ([] if base_domain else
                       [('coordinator_id', '=', self._uid)])
        last_week = dt2str(last_week)
        query = """
        SELECT
          SUM(CASE WHEN create_date > %%s THEN 1 ELSE 0 END) AS today,
          SUM(CASE WHEN create_date <= %%s THEN 1 ELSE 0 END) AS overdue
        FROM
          %s
        %s
        GROUP BY True
        """
        domain = base_domain + [('state', 'in', ('draft', 'sent'))]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['sale.order'], domain)
        query_args = (last_week, last_week) + tuple(where_params)
        self._cr.execute(query % (from_clause, where_str), query_args)
        return self._cr.dictfetchone() or {}

    def _get_purchase_programs(self, base_domain, last_week):
        base_domain = ([] if base_domain else
                       [('manager_id', '=', self._uid)])
        last_week = dt2str(last_week)
        query = """
        SELECT
          SUM(CASE WHEN create_date > %%s THEN 1 ELSE 0 END) AS today,
          SUM(CASE WHEN create_date <= %%s THEN 1 ELSE 0 END) AS overdue
        FROM
          %s
        %s
        GROUP BY True
        """
        domain = base_domain + [('dossier', '=', True),
                                ('open_requisitions', '!=', 0)]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['account.analytic.account'], domain)
        query_args = (last_week, last_week) + tuple(where_params)
        self._cr.execute(query % (from_clause, where_str), query_args)
        return self._cr.dictfetchone() or {}

    def _get_coord_dossiers(self, base_domain, today, next_21_days,
                            next_30_days):
        base_domain = ([] if base_domain else
                       [('manager_id', '=', self._uid)])
        today = dt2str(today)
        next_21_days = dt2str(next_21_days)
        next_30_days = dt2str(next_30_days)
        query = """
        SELECT
            (SELECT
              COUNT(id) count
            FROM
              %s
            %s) as today,
            (SELECT
              COUNT(id) count
            FROM
              %s
            %s) as next_7_days,
            (SELECT
              COUNT(id) count
            FROM
              %s
            %s) as overdue
        """
        domain = base_domain + [
            ('dossier', '=', True),
            ('project_ids.arrival_date', '>', next_21_days),
            ('project_ids.arrival_date', '<=', next_30_days)]
        today_from, today_where, today_params = get_query_from_domain(
            self.env['account.analytic.account'], domain)
        domain = base_domain + [
            ('dossier', '=', True),
            ('project_ids.arrival_date', '>', next_30_days)]
        week_from, week_where, week_params = get_query_from_domain(
            self.env['account.analytic.account'], domain)
        domain = base_domain + [
            ('dossier', '=', True),
            ('project_ids.arrival_date', '>', today),
            ('project_ids.arrival_date', '<=', next_21_days)]
        overdue_from, overdue_where, overdue_params = get_query_from_domain(
            self.env['account.analytic.account'], domain)
        query_args = (today_from, today_where, week_from, week_where,
                      overdue_from, overdue_where)
        where_args = tuple(today_params + week_params + overdue_params)
        self._cr.execute(query % query_args, where_args)
        return self._cr.dictfetchone() or {}

    def _get_close_dossier(self, base_domain, today, last_week, last2_week):
        base_domain = ([] if base_domain else
                       [('manager_id', '=', self._uid)])
        today = dt2str(today)
        last_week = dt2str(last_week)
        last2_week = dt2str(last2_week)
        query = """
        SELECT
          SUM(CASE WHEN date <= %%s AND date > %%s THEN 1 ELSE 0 END) AS today,
          count(id) AS next_7_days,
          SUM(CASE WHEN date <= %%s THEN 1 ELSE 0 END) AS overdue
        FROM
          %s
        %s
        GROUP BY True
        """
        domain = base_domain + [('dossier', '=', True),
                                ('open_requisitions', '=', 0),
                                ('date', '!=', False),
                                ('date', '<=', today)]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['account.analytic.account'], domain)
        query_args = (last_week, last2_week, last2_week) + tuple(where_params)
        self._cr.execute(query % (from_clause, where_str), query_args)
        return self._cr.dictfetchone() or {}

    def _get_indicators(self, base_domain, first_month_day,
                         first_last_month_day, indicators):
        first_month_day = dt2str(first_month_day)
        first_last_month_day = dt2str(first_last_month_day)
        base_domain = ([] if base_domain else
                       [('user_id', '=', self._uid)])
        query = """
            SELECT
              AVG(planification_time) as planification_time,
              AVG(reserve_send_time) as reserve_send_time,
              AVG(supplier_response_time) as supplier_response_time,
              AVG(purchase_time) as purchase_time
            FROM
              %s
            %s
            """
        domain = [
            ('account_analytic_id', '!=', False),
            ('account_analytic_id.create_date', '>=', first_last_month_day),
            ('account_analytic_id.create_date', '<=', first_month_day)]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['xopgi_operations_performance.coordperf_report'],
            base_domain + domain)
        query_args = tuple(where_params)
        self._cr.execute(query % (from_clause, where_str), query_args)
        data = dict()
        data['last_month'] = self._cr.dictfetchone() or {}
        domain = [
            ('account_analytic_id', '!=', False),
            ('account_analytic_id.create_date', '>', first_month_day)]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['xopgi_operations_performance.coordperf_report'],
            base_domain + domain)
        query_args = tuple(where_params)
        self._cr.execute(query % (from_clause, where_str), query_args)
        data['this_month'] = self._cr.dictfetchone() or {}
        res = {}
        for indicator in indicators:
            res[indicator] = {}
            for month in ['this_month', 'last_month']:
                res[indicator][month] = int(
                    data[month].get(indicator, 0) or 0)
        return res


class ResUsers(models.Model):
    _inherit = 'res.users'

    target_planification_time = fields.Integer()
    target_reserve_send_time = fields.Integer()
    target_supplier_response_time = fields.Integer()
    target_purchase_time = fields.Integer()


class ResCompany(models.Model):
    _inherit = 'res.company'

    target_planification_time = fields.Integer()
    target_reserve_send_time = fields.Integer()
    target_supplier_response_time = fields.Integer()
    target_purchase_time = fields.Integer()


class AnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    def _get_requisitions(self):
        purchase_requisition = self.env['purchase.requisition']
        for account in self:
            open_requisitions = purchase_requisition.search_count(
                ['&', ('account_analytic_id', '=', account.id),
                 ('state', 'not in', ['cancel', 'done'])])
            account.open_requisitions = open_requisitions
            account.close_requisitions = account.requisition_count - open_requisitions

    _search_open_requisitions = (lambda self, *args:
                                 self.search_by_requisitions(*args))

    _search_close_requisitions = (lambda self, *args:
                                  self.search_by_requisitions(
                                      *(args + (('done',),))))

    def search_by_requisitions(self, operator, operand,
                               states=('draft', 'in_progress', 'open')):
        if operator in ('=', '!=') and operand == 0:
            purchase_requisition = self.env['purchase.requisition']
            open_requisitions = purchase_requisition.search(
                ['&',
                 ('account_analytic_id.state', 'not in', ['cancelled', 'done']),
                 ('state', 'in', states)]
            )
            account_ids = list({x.account_analytic_id.id
                                for x in open_requisitions
                                if x.account_analytic_id})
            return [('id', 'in' if operator == '=' else 'not in', account_ids)]
        else:
            return []

    open_requisitions = fields.Integer(compute='_get_requisitions',
                                       search='_search_open_requisitions')
    close_requisitions = fields.Integer(compute='_get_requisitions',
                                        search='_search_close_requisitions')
