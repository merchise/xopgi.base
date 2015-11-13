# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2013 OpenERP s.a. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, _
from xoeuf.tools import normalize_date as to_date, dt2str, date2str

    
class CrmLead(models.Model):
    _inherit = 'crm.lead'
    
    @api.model
    def retrieve_sales_dashboard_data(self, mode=None):
        base_domain = ([]
                       if mode and mode == 'company'
                       else [('user_id', '=', self._uid)])
        res = {
            'mode': mode or '',
            'meeting': {'today': 0, 'next_7_days': 0, },
            'lead': {'today': 0, 'overdue': 0, 'next_7_days': 0, },
            'opportunity': {'today': 0, 'overdue': 0, 'next_7_days': 0, },
            'quotation': {'today': 0, 'overdue': 0, 'next_7_days': 0, },
            'sale': {'today': 0, 'overdue': 0, 'next_7_days': 0, },
            'done': {'this_month': 0, 'last_month': 0, 'sector': 0, },
            'won': {'this_month': 0, 'last_month': 0, 'sector': 0, },
            'invoiced': {'this_month': 0, 'last_month': 0, 'sector': 0, },
            'nb_opportunities': 0,
        }
        today = date.today()
        first_month_day = today.replace(day=1)
        first_last_month_day = first_month_day - relativedelta(months=+1)
        next_week = today + timedelta(days=7)
        last_week = today + timedelta(days=-7)
        opportunities = self.search(base_domain)
        for opp in opportunities:
            if opp.type == 'opportunity':
                # Next activities
                if opp.date_action:
                    date_action = to_date(opp.date_action)
                    if date_action == today:
                        res['opportunity']['today'] += 1
                    if today <= date_action <= next_week:
                        res['opportunity']['next_7_days'] += 1
                    if date_action < today:
                        res['opportunity']['overdue'] += 1
                # Won in Opportunities
                if opp.date_closed:
                    date_closed = to_date(opp.date_closed)
                    if today >= date_closed >= first_month_day:
                        if opp.planned_revenue:
                            res['won']['this_month'] += opp.planned_revenue
                    elif first_month_day > date_closed >= \
                            first_last_month_day:
                        if opp.planned_revenue:
                            res['won']['last_month'] += opp.planned_revenue
                # Actions done.
                date_act = to_date(opp.create_date)
                if today >= date_act >= first_month_day:
                    res['done']['this_month'] += 1
                elif first_month_day > date_act >= first_last_month_day:
                    res['done']['last_month'] += 1
            # Leads
            else:
                lead_date = to_date(opp.create_date)
                if lead_date >= last_week:
                    res['lead']['today'] += 1
                if lead_date < last_week:
                    res['lead']['overdue'] += 1
        sales = self.env['sale.order'].search(
            base_domain + [('state', 'not in', ('cancel', 'done'))])
        for sale in sales:
            # Quotations
            if sale.state in ('draft', 'sent', 'cancel'):
                quotation_date = to_date(sale.create_date)
                if last_week <= quotation_date:
                    res['quotation']['today'] += 1
                if quotation_date < last_week:
                    res['quotation']['overdue'] += 1
            # Sales orders
            else:
                if sale.date_order:
                    date_order = to_date(sale.date_order)
                    if date_order == today:
                        res['sale']['today'] += 1
                    if today <= date_order <= next_week:
                        res['sale']['next_7_days'] += 1
                    if date_order < today:
                        res['sale']['overdue'] += 1
        # Meetings
        min_date = dt2str(today)
        max_date = dt2str(today + timedelta(days=8))
        # We need to add 'mymeetings' in the context for the search to 
        # be correct.
        meetings = self.env['calendar.event']
        if base_domain:
            meetings = meetings.with_context(mymeetings=1)
        for meeting in meetings.search(
                [('start', '>=', min_date), ('start', '<=', max_date)]):
            if meeting.start:
                start = to_date(meeting.start)
                if start == today:
                    res['meeting']['today'] += 1
                if today <= start <= next_week:
                    res['meeting']['next_7_days'] += 1
        # Invoiced
        account_invoice_domain = [
            ('state', 'in', ['open', 'paid']),
            ('user_id', '=', self._uid),
            ('date_invoice', '>=', first_last_month_day)]
        for inv in self.env['account.invoice'].search(account_invoice_domain):
            if inv.date_invoice:
                inv_date = to_date(inv.date_invoice)
                if today >= inv_date >= first_month_day:
                    res['invoiced']['this_month'] += inv.amount_untaxed
                elif first_month_day > inv_date >= first_last_month_day:
                    res['invoiced']['last_month'] += inv.amount_untaxed
        res['nb_opportunities'] = len(opportunities)
        target_obj = self.env.user if base_domain else self.env.user.company_id
        res['done']['target'] = target_obj.target_sales_done
        res['won']['target'] = target_obj.target_sales_won
        res['invoiced']['target'] = target_obj.target_sales_invoiced
        res['currency_id'] = self.env.user.company_id.currency_id.id
        for indicator in ['done', 'won', 'invoiced']:
            sector = 11
            target = res[indicator]['target']
            value = res[indicator]['this_month']
            if target:
                if target < value:
                    sector = 10
                else:
                    sector = int(float(value) / target * 10)
            res[indicator]['sector'] = str(sector)
        return res

    @api.model
    def modify_target_sales_dashboard(self, target_name, target_value,
                                      mode=None):
        target_obj = (self.env.user.company_id.sudo()
                      if mode == 'company'
                      else self.env.user.sudo())
        if not target_value:
            target_value = 0
        _super = getattr(super(CrmLead, self),
                         'modify_target_sales_dashboard', False)
        if _super:
            return _super()
        if target_name in ['won', 'done', 'invoiced']:
            return setattr(target_obj,
                           'target_sales_' + target_name,
                           target_value)


class ResUsers(models.Model):
    _inherit = 'res.users'

    target_sales_done = fields.Integer()
    target_sales_won = fields.Integer()
    target_sales_invoiced = fields.Integer()


class ResCompany(models.Model):
    _inherit = 'res.company'

    target_sales_done = fields.Integer()
    target_sales_won = fields.Integer()
    target_sales_invoiced = fields.Integer()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
