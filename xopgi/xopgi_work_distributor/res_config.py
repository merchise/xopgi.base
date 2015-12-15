#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_work_distributor.res_config
# --------------------------------------------------------------------------
# Copyright (c) 2014, 2015 Merchise Autrement and Contributors
# All rights reserved.
#
# Author: Merchise Autrement
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from openerp import api, models, fields
from xoeuf.ui import RELOAD_UI
from xoutil import logger


class WorkDistributionSettings(models.TransientModel):
    _name = 'work.distribution.settings'
    _inherit = 'res.config.settings'

    def _get_default_work_distribution_models(self):
        return self.env['work.distribution.model'].search([]).ids

    models_ids = fields.Many2many(
        'work.distribution.model', 'work_distribution_settings_rel',
        'setting_id', 'model_id', 'Models',
        default=_get_default_work_distribution_models)

    @api.guess
    def install(self, *args, **kargs):
        for wiz in self.browse(*args, **kargs):
            wiz.models_ids.unlink_rest()
        return RELOAD_UI


@api.model
@api.returns('self', lambda value: value.id)
def create(self, vals):
    if 'work.distribution.model' in self.pool:
        self.env['work.distribution.model'].distribute(self._name, vals)
    res = super(models.Model, self).create(vals)
    return res

# NOTICE: We can do this cause models.Model does not have a `create` method
# directly, but inherited from BaseModel.
models.Model.create = create


@api.guess
def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                    context=None, toolbar=False, submenu=False):
    result = super(models.Model, self).fields_view_get(
        cr, uid, view_id=view_id, view_type=view_type, context=context,
        toolbar=toolbar, submenu=submenu)
    if 'work.distribution.model' not in self.pool or view_type != 'form':
        return result
    self = self.browse(cr, uid, None, context=context)
    if not self.user_has_groups(
            'xopgi_work_distributor.group_distributor_manager,'
            'base.group_system'):
        return result
    distribution_models = self.env['work.distribution.model'].search(
        [('group_field.relation', '=', self._name)])
    if not distribution_models:
        return result
    try:
        temp = dict(result)
        fields_to_add = {}
        for dist_model in distribution_models:
            fields_to_add.update({
                dist_model.strategy_field.name:
                    "<field name='{field_name}' "
                    "domain=\"[('id', 'in', {strategy_ids})]\"/>".format(
                        field_name=dist_model.strategy_field.name,
                        strategy_ids=dist_model.strategy_ids.ids)})
        view_part = "<group>%s</group>"
        arch = temp['arch'].decode('utf8')
        xpath = '</sheet>'
        if arch.find(xpath):
            view_part += xpath
        elif arch.find('<footer'):
            xpath = '<footer'
            view_part = xpath + view_part
        else:
            xpath = '</form>'
            view_part += xpath

        temp['arch'] = arch.replace(
            xpath, view_part % '\t'.join(fields_to_add.values()))
        temp['fields'].update(self.fields_get(fields_to_add.keys()))
        result = temp
    except:
        logger.exception(
            'An error happen trying to add work distribution strategy '
            'fields on form view for '
            'Model: %s.' % (self._name))
    return result


# NOTICE: We can do this cause models.Model does not have a `fields_view_get`
# method directly, but inherited from BaseModel.
models.Model.fields_view_get = fields_view_get
