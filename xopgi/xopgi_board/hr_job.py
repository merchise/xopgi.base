# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.hr_job
# ---------------------------------------------------------------------
# Copyright (c) 2014, 2015 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2015-11-12

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from openerp import fields, models


class HrJob(models.Model):
    _inherit = 'hr.job'
    widgets = fields.One2many('hr.job.widget', 'job_position')
    contracts_ids = fields.One2many('hr.contract', 'job_id')


class HrJobWidget(models.Model):
    _name = 'hr.job.widget'
    _order = 'job_position, priority'

    job_position = fields.Many2one('hr.job', required=True)
    widget = fields.Many2one('xopgi.board.widget', delegate=True,
                             required=True, ondelete='cascade')
    priority = fields.Integer(default=1000)

    def get_user_widgets(self):
        job_widgets = self.env['hr.job.widget'].search_read(
            domain=[('job_position.contracts_ids.employee_id.user_id', '=',
                    self._uid)],
            fields=['name', 'category', 'template_name', 'xml_template',
                    'python_code'], order='priority')
        widgets = []
        for job_widget in job_widgets:
            job_widget.pop('id', None)
            if job_widget not in widgets:
                widgets.append(job_widget)
        return widgets
