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
from openerp import api, models, fields


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
        return {'type': 'ir.actions.client', 'tag': 'reload', }

@api.model
@api.returns('self', lambda value: value.id)
def create(self, vals):
    if 'work.distribution.model' in self.pool:
        self.env['work.distribution.model'].distribute(self._name, vals)
    res = super(models.Model, self).create(vals)
    return res


models.Model.create = create


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
