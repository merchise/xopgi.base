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

from openerp import fields, models


class HrJob(models.Model):
    _inherit = 'hr.job'

    widgets = fields.Many2many('xopgi.board.widget')
