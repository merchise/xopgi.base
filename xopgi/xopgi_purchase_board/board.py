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
from openerp import api, fields, models, _
from openerp.addons.xopgi_board.board import lineal_color_scaling
from xoeuf.tools import normalize_date as to_date, dt2str, date2str


class PurchaseBoard(models.AbstractModel):
    _name = 'purchase.board'

    @api.model
    def get_data(self, mode=None):
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
        today = date.today()
        first_month_day = today.replace(day=1)
        first_last_month_day = first_month_day - relativedelta(months=+1)
        next_21_days = today + timedelta(days=21)
        next_30_days = today + timedelta(days=30)
        last_week = today + timedelta(days=-7)
        next_week = today + timedelta(days=7)
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
        for po in self.env['purchase.order'].search(
                [('minimum_planned_date', '!=', False),
                 ('minimum_planned_date', '>=', dt2str(today)),
                 ('minimum_planned_date', '<=', dt2str(next_30_days))] + (
                    [] if mode else [('user_id', '=', self._uid)])):
            #  Presupuestos a confirmar y por facturar
            po_date = to_date(po.minimum_planned_date)
            if po_date <= next_week:
                res['confirm_order']['overdue'] += 1
                if po.open:
                    res['not_invoiced']['overdue'] += 1
            elif last_week < po_date <= next_21_days:
                res['confirm_order']['today'] += 1
                if po.open:
                    res['not_invoiced']['today'] += 1
            if last_week < po_date <= next_21_days:
                res['confirm_order']['next_7_days'] += 1
                if po.open:
                    res['not_invoiced']['next_7_days'] += 1
        #indicadores
        indicators = ['reserve_send_time', 'supplier_response_time',
                      'purchase_time']
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
