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

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from openerp import api, models
from openerp.addons.xopgi_board.board import lineal_color_scaling, \
    get_query_from_domain, get_targets
from xoeuf.tools import normalize_date as to_date, dt2str, date2str
from xoutil import logger


class ProjectBoard(models.AbstractModel):
    _name = 'project.board'

    @api.model
    def get_data(self, today, mode=None):
        base_domain = ([]
                       if mode and mode == 'company'
                       else ['|', ('user_id', '=', False),
                             ('user_id', '=', self._uid)])
        res = {
            'mode': mode if base_domain else '',
            'task': {'today': 0, 'overdue': 0, 'next_7_days': 0, 'new': 0,
                     'unassigned': 0, 'unread': 0},
            'issue': {'overdue': 0, 'no_activity': 0, 'new': 0,
                      'unassigned': 0, 'unread': 0},
        }
        tomorrow = dt2str(today + timedelta(days=1))
        next_8_days = dt2str(today + timedelta(days=8))
        first_month_day = today.replace(day=1)
        first_last_month_day = dt2str(
            first_month_day - relativedelta(months=+1))
        first_month_day = dt2str(first_month_day)
        # Task
        logger.debug('Starting to search tasks')
        res['task'].update(
            self._get_tasks(base_domain, today, tomorrow, next_8_days))
        # Issue
        logger.debug('Starting to search tasks')
        res['issue'].update(
            self._get_issues(base_domain, first_last_month_day,
                             first_month_day))
        return res

    def _get_tasks(self, base_domain, today, tomorrow, next_8_days):
        query = """
        SELECT
            SUM(CASE WHEN user_id IS NULL
                THEN 1 ELSE 0 END) AS unassigned,
            SUM(CASE WHEN user_id IS NOT NULL AND date_end IS NOT NULL AND
                date_end < %%s THEN 1 ELSE 0 END) AS overdue,
            SUM(CASE WHEN user_id IS NOT NULL AND date_end IS NOT NULL AND
                date_end >= %%s AND date_end < %%s
                THEN 1 ELSE 0 END) AS today,
            SUM(CASE WHEN user_id IS NOT NULL AND date_end IS NOT NULL AND
                date_end >= %%s AND date_end < %%s
                THEN 1 ELSE 0 END) AS next_7_days
        FROM
            %s
        %s
        """
        domain = base_domain + [('stage_id.closed', '=', False)]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['project.task'], domain)
        query_args = (today, today, tomorrow, today, next_8_days
                      ) + tuple(where_params)
        self._cr.execute(query % (from_clause, where_str), query_args)
        data = self._cr.dictfetchone() or {}
        query = "SELECT COUNT(id) AS new FROM %s %s"
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['project.task'], [('stage_id.sequence', '=', 1)])
        self._cr.execute(query % (from_clause, where_str), where_params)
        data.update(self._cr.dictfetchone() or {})
        query = "SELECT COUNT(project_task.id) AS unread FROM %s %s"
        unread_domain = domain + [('message_unread', '=', True)]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['project.task'], unread_domain)
        self._cr.execute(query % (from_clause, where_str), where_params)
        data.update(self._cr.dictfetchone() or {})
        return data

    def _get_issues(self, base_domain, first_last_month_day, first_month_day):
        query = """
        SELECT
            SUM(CASE WHEN user_id IS NULL
                THEN 1 ELSE 0 END) AS unassigned,
            SUM(CASE WHEN user_id IS NOT NULL AND
                create_date < %%s THEN 1 ELSE 0 END) AS overdue,
            SUM(CASE WHEN user_id IS NOT NULL AND
                message_last_post IS NOT NULL AND message_last_post < %%s
                THEN 1 ELSE 0 END) AS no_activity
        FROM
            %s
        %s
        """
        domain = base_domain + [('stage_id.closed', '=', False)]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['project.issue'], domain)
        query_args = (first_last_month_day, first_month_day
                     ) + tuple(where_params)
        self._cr.execute(query % (from_clause, where_str), query_args)
        data = self._cr.dictfetchone() or {}
        query = "SELECT COUNT(id) AS new FROM %s %s"
        new_domain = domain + [('stage_id.sequence', '<=', 1)]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['project.issue'], new_domain)
        self._cr.execute(query % (from_clause, where_str), where_params)
        data.update(self._cr.dictfetchone() or {})
        query = "SELECT COUNT(project_issue.id) AS unread FROM %s %s"
        unread_domain = domain + [('message_unread', '=', True)]
        from_clause, where_str, where_params = get_query_from_domain(
            self.env['project.issue'], unread_domain)
        self._cr.execute(query % (from_clause, where_str), where_params)
        data.update(self._cr.dictfetchone() or {})
        return data

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
