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


class ProjectBoard(models.AbstractModel):
    _name = 'project.board'

    @api.model
    def get_data(self, mode=None):
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
        today = date.today()
        next_week = today + timedelta(days=7)
        first_month_day = today.replace(day=1)
        first_last_month_day = first_month_day - relativedelta(months=+1)
        # Task
        for task in self.env['project.task'].search(
                [('stage_id.closed', '=', False)] + base_domain):
            if not task.user_id:
                res['task']['unassigned'] += 1
            if task.user_id or not base_domain:
                if task.date_end:
                    date_end = to_date(task.date_end)
                    if date_end <= today:
                        res['task']['overdue'] += 1
                    elif date_end <= next_week:
                        res['task']['next_7_days'] += 1
                        if date_end == today:
                            res['task']['today'] += 1
                if task.stage_id.sequence <= 1:
                    res['task']['new'] += 1
                if task.message_unread:
                    res['task']['unread'] += 1
        # Issue
        for issue in self.env['project.issue'].search(
                [('stage_id.closed', '=', False)] + base_domain):
            if not issue.user_id:
                res['issue']['unassigned'] += 1
            if issue.user_id or not base_domain:
                if to_date(issue.create_date) <= first_last_month_day:
                    res['issue']['overdue'] += 1
                if (issue.message_last_post and to_date(
                        issue.message_last_post) <= first_month_day):
                    res['issue']['no_activity'] += 1
                if issue.stage_id.sequence <= 1:
                    res['issue']['new'] += 1
                if issue.message_unread:
                    res['issue']['unread'] += 1
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
