#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_work_distributor.res_config
# --------------------------------------------------------------------------
# Copyright (c) 2014-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# Author: Merchise Autrement [~º/~]
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.

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

    def _get_default_work_distribution_models(self):
        return self.env[WORKDIST_MODELNAME].search([]).ids

    models_ids = fields.Many2many(
        WORKDIST_MODELNAME, 'work_distribution_settings_rel',
        'setting_id', 'model_id', 'Models',
        default=_get_default_work_distribution_models)

    @api.guess
    def install(self, *args, **kargs):
        for wiz in self.browse(*args, **kargs):
            wiz.models_ids.unlink_rest()
        return RELOAD_UI


# TODO: The name of the function should not mimic that of the receiver, but
# provide a clue at what is going to happen post fields_view_get
@signals.receiver(signals.post_fields_view_get)
def post_fields_view_get(self, **kwargs):
    result = kwargs['result']
    if WORKDIST_MODELNAME not in self.env or kwargs['view_type'] != 'form':
        return kwargs['result']
    if not self.user_has_groups(
            'xopgi_work_distributor.group_distributor_manager,'
            'base.group_system'):
        return result
    distribution_models = self.env[WORKDIST_MODELNAME].search(
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
        result.update(temp)
    except:
        logger.exception(
            'An error happen trying to add work distribution strategy '
            'fields on form view for '
            'Model: %s.' % (self._name))
    return result
