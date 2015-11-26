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
from openerp.addons.xopgi_board.board import lineal_color_scaling, \
    get_query_from_domain, get_targets
from xoeuf.tools import dt2str, date2str, normalize_datetime
from xoutil import logger


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
            'sale_margin': {'this_month': 0, 'last_month': 0, 'sector': 0, },
            'sale_pax_margin': {'this_month': 0, 'last_month': 0, 'sector': 0, },
            'sale_done': {'this_month': 0, 'last_month': 0, 'color': '', },
            'sale_won': {'this_month': 0, 'last_month': 0, 'color': '', },
            'sale_invoiced': {'this_month': 0, 'last_month': 0, 'color': '', },
        }
        today = date.today()
        first_month_day = today.replace(day=1)
        first_last_month_day = date2str(
            first_month_day - relativedelta(months=+1))
        first_month_day = date2str(first_month_day)
        next_week = date2str(today + timedelta(days=7))
        last_week = date2str(today + timedelta(days=-7))
        today = date2str(today)
        # Meetings
        min_date = dt2str(today)
        max_date = dt2str(date.today() + timedelta(days=8))
        # We need to add 'mymeetings' in the context for the search to
        # be correct.
        meetings = self.env['calendar.event']
        if base_domain:
            meetings = meetings.with_context(mymeetings=1)
        for meeting in meetings.search(
                [('start', '>=', min_date), ('start', '<', max_date)]):
            if meeting.start:
                start = meeting.start[:fields.DATE_LENGTH]
                if start == today:
                    res['meeting']['today'] += 1
                else:
                    res['meeting']['next_7_days'] += 1
        #  Leads
        logger.debug('Starting to search leads')
        res['lead'].update(
            self._get_leads(base_domain, last_week))
        #  Opportunities
        logger.debug('Starting to search opportunities')
        res['opportunity'].update(
            self._get_opportunities(base_domain, today, next_week))
        # Quotations
        logger.debug('Starting to search quotations')
        res['quotation'].update(self._get_quotations(base_domain, last_week))
        #  Sales Orders
        logger.debug('Starting to search sales orders')
        res['sale'].update(
            self._get_sale_orders(base_domain, today, next_week))
        #  Sales done
        logger.debug('Starting to search sales done')
        res['sale_done'].update(
            self._get_sale_done(base_domain, first_month_day,
                                first_last_month_day))
        #  Won Opportunities
        logger.debug('Starting to search won opportunities')
        res['sale_won'].update(
            self._get_won_opp(base_domain, today, first_month_day,
                              first_last_month_day))
        logger.debug('Starting to search meetings')
        # Invoiced
        logger.debug('Starting to search invoices')
        res['sale_invoiced'].update(self._get_sale_invoiced(
            base_domain, today, first_month_day, first_last_month_day))
        logger.debug('Starting to search for operations results')
        # sale_margin
        logger.debug('Starting to search sales margin')
        temp = self._get_sale_margin(base_domain, today, first_month_day,
                                     first_last_month_day)
        res['sale_margin'].update(temp.get('sale_margin', {}))
        res['sale_pax_margin'].update(temp.get('sale_pax_margin', {}))
        # targets
        logger.debug('Getting targets')
        indicators = ['sale_margin', 'sale_pax_margin', 'sale_done',
                      'sale_won', 'sale_invoiced']
        get_targets(self, res, indicators, (not base_domain))
        res['currency_id'] = self.env.user.company_id.currency_id.id
        return res

    def _get_leads(self, base_domain, last_week):
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
        domain = base_domain + [('type', '=', 'lead')]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['crm.lead'], domain)
        query_args = (last_week, last_week) + tuple(where_params)
        self._cr.execute(query % (from_clause, where_str), query_args)
        return self._cr.dictfetchone() or {}

    def _get_opportunities(self, base_domain, today, next_week):
        query = """
        SELECT
          SUM(CASE WHEN date_action = %%s THEN 1 ELSE 0 END) AS today,
          SUM(CASE WHEN date_action > %%s THEN 1 ELSE 0 END) AS next_7_days,
          SUM(CASE WHEN date_action < %%s THEN 1 ELSE 0 END) AS overdue
        FROM
          %s
        %s
        GROUP BY True
        """
        domain = base_domain + [
            ('type', '=', 'opportunity'),
            ('date_action', '!=', False),
            ('date_action', '<=', next_week)]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['crm.lead'], domain)
        query_args = (today, today, today) + tuple(where_params)
        self._cr.execute(query % (from_clause, where_str), query_args)
        return self._cr.dictfetchone() or {}

    def _get_quotations(self, base_domain, last_week):
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

    def _get_sale_orders(self, base_domain, today, next_week):
        query = """
        SELECT
          SUM(CASE WHEN date_order = %%s THEN 1 ELSE 0 END) AS today,
          SUM(CASE WHEN date_order > %%s THEN 1 ELSE 0 END) AS next_7_days,
          SUM(CASE WHEN date_order < %%s THEN 1 ELSE 0 END) AS overdue
        FROM
          %s
        %s
        GROUP BY True
        """
        domain = base_domain + [
            ('state', 'not in', ('cancel', 'sale_done', 'draft', 'sent')),
            ('date_order', '!=', False),
            ('date_order', '<=', next_week)]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['sale.order'], domain)
        query_args = (today, today, today) + tuple(where_params)
        self._cr.execute(query % (from_clause, where_str), query_args)
        return self._cr.dictfetchone() or {}

    def _get_won_opp(self, base_domain, today, first_month_day,
                     first_last_month_day):
        today = dt2str(today)
        first_month_day = dt2str(first_month_day)
        first_last_month_day = dt2str(first_last_month_day)
        query = """
        SELECT
          SUM(CASE WHEN date_closed >= %%s
              THEN planned_revenue ELSE 0 END) AS this_month,
          SUM(CASE WHEN date_closed < %%s
              THEN planned_revenue ELSE 0 END) AS last_month
        FROM
          %s
        %s
        GROUP BY True
        """
        domain = base_domain + [
            ('type', '=', 'opportunity'),
            ('date_closed', '!=', False),
            ('date_closed', '>=', first_last_month_day),
            ('date_closed', '<=', today)]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['crm.lead'], domain)
        query_args = (first_month_day, first_month_day) + tuple(where_params)
        self._cr.execute(query % (from_clause, where_str), query_args)
        return self._cr.dictfetchone() or {}

    def _get_sale_done(self, base_domain, first_month_day,
                       first_last_month_day):
        first_month_day = dt2str(first_month_day)
        first_last_month_day = dt2str(first_last_month_day)
        query = """
        SELECT
          SUM(CASE WHEN create_date >= %%s THEN 1 ELSE 0 END) AS this_month,
          SUM(CASE WHEN create_date < %%s THEN 1 ELSE 0 END) AS last_month
        FROM
          %s
        %s
        GROUP BY True
        """
        domain = base_domain + [
            ('type', '=', 'opportunity'),
            ('create_date', '!=', False),
            ('create_date', '>=', dt2str(first_last_month_day))]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['crm.lead'], domain)
        query_args = (first_month_day, first_month_day) + tuple(where_params)
        self._cr.execute(query % (from_clause, where_str), query_args)
        return self._cr.dictfetchone() or {}

    def _get_sale_margin(self, base_domain, today, first_month_day,
                           first_last_month_day):
        base_domain = ([('primary_salesperson_id', '=', self._uid)]
                       if base_domain else [])
        inv_query = """
            SELECT
              CASE WHEN this_month_count IS NOT NULL AND this_month_count > 0
                   THEN this_month_balance / this_month_count
                   ELSE 0 END AS this_month_margin,
              CASE WHEN last_month_count IS NOT NULL AND last_month_count > 0
                   THEN last_month_balance / last_month_count
                   ELSE 0 END AS last_month_margin,

              CASE WHEN this_month_pax_count IS NOT NULL AND
                        this_month_pax_count > 0
                   THEN this_month_pax_balance / this_month_pax_count
                   ELSE 0 END AS this_month_margin_pax,
              CASE WHEN last_month_pax_count IS NOT NULL AND
                        last_month_pax_count > 0
                   THEN last_month_pax_balance / last_month_pax_count
                   ELSE 0 END AS last_month_margin_pax
            FROM
                (SELECT
                  SUM(CASE WHEN date >= %%s
                      THEN balance ELSE 0 END) AS this_month_balance,
                  SUM(CASE WHEN date >= %%s
                      THEN 1 ELSE 0 END) AS this_month_count,
                  SUM(CASE WHEN date < %%s
                      THEN balance ELSE 0 END) AS last_month_balance,
                  SUM(CASE WHEN date < %%s
                      THEN 1 ELSE 0 END) AS last_month_count,
                  SUM(CASE WHEN date >= %%s AND pax > 0
                      THEN balance * pax ELSE 0 END) AS this_month_pax_balance,
                  SUM(CASE WHEN date >= %%s AND pax > 0
                      THEN pax ELSE 0 END) AS this_month_pax_count,
                  SUM(CASE WHEN date < %%s AND pax > 0
                      THEN balance * pax ELSE 0 END) AS last_month_pax_balance,
                  SUM(CASE WHEN date < %%s AND pax > 0
                      THEN pax ELSE 0 END) AS last_month_pax_count
                FROM
                  %s
                %s) sub
            """
        account_invoice_domain = [
            ('date', '!=', False),
            ('date', '>=', first_last_month_day),
            ('date', '<=', today)]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['xopgi_operations_performance.opresult_report'],
            base_domain + account_invoice_domain)
        query_args = (tuple([first_month_day for i in range(8)]) +
                      tuple(where_params))
        self._cr.execute(inv_query % (from_clause, where_str), query_args)
        data = self._cr.dictfetchone() or {}
        res = {
            'sale_margin': {'this_month': 0, 'last_month': 0},
            'sale_pax_margin': {'this_month': 0, 'last_month': 0}
        }
        res['sale_margin']['this_month'] = data.get('this_month_margin', 0.0)
        res['sale_margin']['last_month'] = data.get('last_month_margin', 0.0)
        res['sale_pax_margin']['this_month'] = data.get(
            'this_month_margin_pax', 0.0)
        res['sale_pax_margin']['last_month'] = data.get(
            'last_month_margin_pax', 0.0)
        return res

    def _get_sale_invoiced(self, base_domain, today, first_month_day,
                           first_last_month_day):
        inv_query = """
            SELECT
              SUM(CASE WHEN date >= %%s
                    THEN price_total
                  ELSE
                    0
                  END) AS this_month,
              SUM(CASE WHEN date < %%s
                    THEN price_total
                  ELSE
                    0
                  END) AS last_month
            FROM
              %s
            %s
            GROUP BY True
            """
        account_invoice_domain = [
            ('state', 'not in', ('draft', 'cancel', 'proforma', 'proforma2')),
            ('date', '!=', False), ('date', '>=', first_last_month_day),
            ('date', '<=', today),
            ('type', 'in', ('out_invoice', 'out_refund'))]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['account.invoice.report'],
            base_domain + account_invoice_domain)
        query_args = (first_month_day, first_month_day) + tuple(where_params)
        self._cr.execute(inv_query % (from_clause, where_str), query_args)
        return self._cr.dictfetchone() or {}


class ResUsers(models.Model):
    _inherit = 'res.users'

    target_sale_margin = fields.Integer()
    target_sale_pax_margin = fields.Integer()
    target_sale_done = fields.Integer()
    target_sale_won = fields.Integer()
    target_sale_invoiced = fields.Integer()


class ResCompany(models.Model):
    _inherit = 'res.company'

    target_sale_margin = fields.Integer()
    target_sale_pax_margin = fields.Integer()
    target_sale_done = fields.Integer()
    target_sale_won = fields.Integer()
    target_sale_invoiced = fields.Integer()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
