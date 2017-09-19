# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.res_group
# ---------------------------------------------------------------------
# Copyright (c) 2016-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-07-07

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoeuf import fields, models
from xoeuf.models import get_modelname
from .board_widget import WIDGET_REL_MODEL_NAME

try:
    from xoeuf.odoo.addons.base.res.res_users import Groups as res_groups
except:
    # odoo 8
    from xoeuf.odoo.addons.base.res.res_users import res_groups


class ResGroup(models.Model):
    _inherit = get_modelname(res_groups)
    widgets = fields.One2many('res.group.widget', 'group')


class ResGroupWidget(models.Model):
    _name = 'res.group.widget'
    _order = 'group, priority'
    _inherit = WIDGET_REL_MODEL_NAME

    group = fields.Many2one(get_modelname(res_groups), required=True)

    def get_user_widgets(self):
        '''Returns the groups in which the current user is located

        '''
        return self.search([('group.users', '=', self._uid)])
