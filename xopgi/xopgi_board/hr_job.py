#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoeuf import fields, models
from .board_widget import WIDGET_REL_MODEL_NAME


class HrJob(models.Model):
    _inherit = 'hr.job'

    widgets = fields.One2many('hr.job.widget', 'job_position')

    # The reverse of the job_id from hr.contract.
    contract_ids = fields.One2many('hr.contract', 'job_id')


class HrJobWidget(models.Model):
    _name = 'hr.job.widget'
    _order = 'job_position, priority'
    _inherit = WIDGET_REL_MODEL_NAME

    job_position = fields.Many2one('hr.job', required=True)

    def get_user_widgets(self):
        user_id = 'job_position.contract_ids.employee_id.user_id'
        return self.search([(user_id, '=', self._uid)])
