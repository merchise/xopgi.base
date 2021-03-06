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

from xoeuf.odoo import api, fields, models


class NewEvent(models.TransientModel):
    _name = 'cdr.new.event'

    event_type = fields.Selection(selection='_get_specific_event_models',
                                  required=True)

    def _get_specific_event_models(self):
        result = []
        for model in self.env['cdr.system.event'].get_specific_event_models():
            result.append((model._name, model._description or model._name))
        return result

    @api.multi
    def create_event(self):
        return dict(
            type='ir.actions.act_window',
            view_type='form',
            view_mode='form',
            res_model=self.event_type,
        )
