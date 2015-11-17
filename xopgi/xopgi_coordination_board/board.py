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
from openerp.addons.xopgi_board.board import lineal_color_scaling
from xoeuf.tools import normalize_date as to_date, dt2str, date2str


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
        for quotation in self.env['sale.order'].search(
                [('state', 'in', ('draft', 'sent'))] +
                    ([] if mode else [('coordinator_id', '=', self._uid)])):
            # Presupuestos de venta a confirmar
            quotation_date = to_date(quotation.create_date)
            if quotation_date <= last_week:
                res['quotation']['overdue'] += 1
            else:
                res['quotation']['today'] += 1
        for dossier in self.env['account.analytic.account'].search(
                [('dossier', '=', True)] + (
                    [] if mode else [('manager_id', '=', self._uid)])):
            # Programas de compra
            if dossier.open_requisitions:
                dossier_date = to_date(dossier.create_date)
                if dossier_date <= last_week:
                    res['program']['overdue'] += 1
                else:
                    res['program']['today'] += 1
            # Dossier a coordinar
            elif dossier.project_ids and dossier.project_ids[0].arrival_date:
                arrival_date = to_date(dossier.project_ids[0].arrival_date)
                if arrival_date > today:
                    if arrival_date <= next_21_days:
                        res['coord_dossier']['overdue'] += 1
                    else:
                        res['coord_dossier']['next_7_days'] += 1
                        if arrival_date <= next_30_days:
                            res['coord_dossier']['today'] += 1
            # Dossier a cerrar
            elif dossier.date:
                depart_date = to_date(dossier.date)
                if depart_date <= last2_week:
                    res['close_dossier']['overdue'] += 1
                elif depart_date < today:
                    res['close_dossier']['next_7_days'] += 1
                    if depart_date <= last_week:
                        res['close_dossier']['today'] += 1
        #indicadores
        indicators = ['planification_time', 'reserve_send_time',
                      'supplier_response_time', 'purchase_time']
        operation_count = {'this_month': 0, 'last_month': 0}
        indicator_sum = {indicator: dict(operation_count)
                         for indicator in indicators}
        for operation in self.env[
                'xopgi_operations_performance.coordperf_report'].search(
                [('account_analytic_id.create_date', '>=', dt2str(
                    first_last_month_day))] +
                    ([] if mode else [('user_id', '=', self._uid)])):
            op_date = to_date(operation.account_analytic_id.create_date)
            position = ('this_month'
                        if today >= op_date >= first_month_day
                        else 'last_month')
            for indicator in indicators:
                value = getattr(operation, indicator, 0)
                if value:
                    indicator_sum[indicator][position] += value
            operation_count[position] += 1
        for position in operation_count.keys():
            for indicator in indicators:
                res[indicator][position] = (float(
                    indicator_sum[indicator][position] / operation_count[position])
                    if operation_count[position] else 0.00)
        target_obj = self.env.user.company_id if mode else self.env.user
        for indicator in indicators:
            sector = 11
            res[indicator]['target'] = target = getattr(
                target_obj, 'target_%s' % indicator, 0)
            value = res[indicator]['this_month']
            if target:
                if target < value:
                    sector = 1.0
                else:
                    sector = float(value) / target
            if sector > 1.0:
                color = '#e2e2e0'
            else:
                color = 'rgb(%s, %s, %s)' % lineal_color_scaling(sector)
            res[indicator]['color'] = color
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
