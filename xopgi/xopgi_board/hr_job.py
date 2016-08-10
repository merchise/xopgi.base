# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.hr_job
# ---------------------------------------------------------------------
# Copyright (c) 2014, 2015 Merchise Autrement [~º/~] and Contributors
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
from .board_widget import WIDGET_REL_MODEL_NAME


class HrJob(models.Model):
    _inherit = 'hr.job'

    widgets = fields.One2many('hr.job.widget', 'job_position')


class HrJobWidget(models.Model):
    _name = 'hr.job.widget'
    _order = 'job_position, priority'
    _inherit = WIDGET_REL_MODEL_NAME

    job_position = fields.Many2one('hr.job', required=True)

    def get_user_widgets(self):
        return self.search([
            ('job_position.contract_ids.employee_id.user_id', '=', self._uid)
        ])
