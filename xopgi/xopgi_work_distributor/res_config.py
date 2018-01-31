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

from xoeuf import signals, api, models, fields
from xoeuf.ui import RELOAD_UI

from .work_distributor import WORKDIST_MODELNAME

import logging
logger = logging.getLogger(__name__)
del logging


class WorkDistributionSettings(models.TransientModel):
    _name = 'work.distribution.settings'
    _inherit = 'res.config.settings'

    @api.multi
    def _set_work_distribution(self):
        models = self.mapped('models_ids')
        models.unlink_rest()
        self.invalidate_cache()

    def _compute_work_distribution_models(self):
        for settings in self:
            settings.models_ids = self._get_work_distribution_models()

    @api.model
    def _get_work_distribution_models(self):
        return self.env[WORKDIST_MODELNAME].search([]).ids

    models_ids = fields.Many2many(
        WORKDIST_MODELNAME,
        string='Models',
        compute=_compute_work_distribution_models,
        inverse=_set_work_distribution,
        default=_get_work_distribution_models
    )

    @api.multi
    def install(self):
        self._set_work_distribution()
        return RELOAD_UI


@signals.receiver(signals.post_fields_view_get)
def _inject_work_distribution_fields(self, signal, **kwargs):
    result = kwargs['result']
    if kwargs['view_type'] != 'form':
        return kwargs['result']
    if not self.user_has_groups(
            'xopgi_work_distributor.group_distributor_manager,'
            'base.group_system'):
        return result
    distribution_models = self.env[WORKDIST_MODELNAME].search(
        [('group_field.relation', '=', self._name)])
    if not distribution_models:
        return result
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
    result.update(temp)
    return result
