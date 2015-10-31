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

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, _
from xoeuf.tools import normalize_date as to_date, dt2str, date2str


class XopgiBoard(models.Model):
    _inherit = 'xopgi.board'
    _description = "Board"

    @api.model
    def get_data(self):
        """Override this method to add new board widget.
        :return: list of dict like {
            'template': 'template_x',  # qweb template to show
            'string': 'widget x',  # title of widget
            'values': {},  # dict with values to show
        }
        """
        res = super(XopgiBoard, self).get_data()
        # get values
        values = self.env['crm.lead'].retrieve_sales_dashboard()
        return res + [dict(
            template='sales_team.SalesDashboard',
            string=_('Sales'),
            values=values,
        )]
    
    
class CrmLead(models.Model):
    _inherit = 'crm.lead'
    
    @api.model
    def retrieve_sales_dashboard(self):
        _super = getattr(super(CrmLead, self), 'retrieve_sales_dashboard', 
                         False) 
        if _super:
            return _super()
        res = {
            'meeting': {'today': 0, 'next_7_days': 0, },
            'activity': {'today': 0, 'overdue': 0, 'next_7_days': 0, },
            'closing': {'today': 0, 'overdue': 0, 'next_7_days': 0, },
            'done': {'this_month': 0, 'last_month': 0, },
            'won': {'this_month': 0, 'last_month': 0, },
            'nb_opportunities': 0,
            'invoiced': {'this_month': 0, 'last_month': 0, }
        }
        today = date.today()
        first_month_day = today.replace(day=1)
        first_last_month_day = first_month_day - relativedelta(months=+1)
        next_week = today + timedelta(days=7)
        opportunities = self.search(
            [('type', '=', 'opportunity'), ('user_id', '=', self._uid)])
        for opp in opportunities:
            # Expected closing
            if opp.date_deadline:
                date_deadline = to_date(opp.date_deadline)

                if date_deadline == today:
                    res['closing']['today'] += 1
                if today <= date_deadline <= next_week:
                    res['closing']['next_7_days'] += 1
                if date_deadline < today:
                    res['closing']['overdue'] += 1
            # Next activities
            if opp.date_action:
                date_action = to_date(opp.date_action)
                if date_action == today:
                    res['activity']['today'] += 1
                if today <= date_action <= next_week:
                    res['activity']['next_7_days'] += 1
                if date_action < today:
                    res['activity']['overdue'] += 1
            # Won in Opportunities
            if opp.date_closed:
                date_closed = to_date(opp.date_closed)
                if today >= date_closed >= first_month_day:
                    if opp.planned_revenue:
                        res['won']['this_month'] += opp.planned_revenue
                elif first_month_day > date_closed >= first_last_month_day:
                    if opp.planned_revenue:
                        res['won']['last_month'] += opp.planned_revenue
        # crm.activity is a very messy model so we need to do that in
        # order to retrieve the actions done.
        self._cr.execute("""
            SELECT m.id, m.subtype_id, m.date, l.user_id, l.type
            FROM "mail_message" m
            LEFT JOIN "crm_lead" l ON (m.res_id = l.id)
            WHERE (m.model = 'crm.lead') AND (l.user_id = %s) AND
                  (l.type = 'opportunity')
        """, (self._uid,))
        activites_done = self._cr.dictfetchall()
        for act in activites_done:
            if act['date']:
                date_act = to_date(act['date'])
                if today >= date_act >= first_month_day:
                    res['done']['this_month'] += 1
                elif first_month_day > date_act >= first_last_month_day:
                    res['done']['last_month'] += 1
        # Meetings
        min_date = dt2str(datetime.now())
        max_date = dt2str(datetime.now() + timedelta(days=8))
        meetings_domain = [('start', '>=', min_date),
            ('start', '<=', max_date)]
        # We need to add 'mymeetings' in the context for the search to 
        # be correct.
        meetings = self.with_context(mymeetings=1).env['calendar.event']
        for meeting in meetings.search(meetings_domain):
            if meeting.start:
                start = to_date(meeting.start)
                if start == today:
                    res['meeting']['today'] += 1
                if today <= start <= next_week:
                    res['meeting']['next_7_days'] += 1
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
        res['done']['target'] = self.env.user.target_sales_done
        res['won']['target'] = self.env.user.target_sales_won
        res['invoiced']['target'] = self.env.user.target_sales_invoiced
        res['currency_id'] = self.env.user.company_id.currency_id.id
        return res

    @api.model
    def modify_target_sales_dashboard(self, target_name, target_value):
        if not target_value:
            target_value = 0
        _super = getattr(super(CrmLead, self),
                         'modify_target_sales_dashboard', False)
        if _super:
            return _super()
        if target_name in ['won', 'done', 'invoiced']:
            return setattr(self.env.user.sudo(),
                           'target_sales_' + target_name,
                           target_value)


class ResUsers(models.Model):
    _inherit = 'res.users'

    target_sales_done = fields.Integer()
    target_sales_won = fields.Integer()
    target_sales_invoiced = fields.Integer()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
