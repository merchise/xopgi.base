# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_directory.res_config
# ---------------------------------------------------------------------
# Copyright (c) 2013-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _absolute_import)


from openerp import api, fields, models


class DirectoryConfig(models.TransientModel):
    _name = 'directory.config'
    _inherit = 'res.config.settings'

    models = fields.Many2many(
        'contact.reference.model',
        default=lambda self: self.env['contact.reference.model'].search([]))

    @api.multi
    def execute(self):
        self.env['contact.reference.model'].search(
            [('id', 'not in', self.models.ids)]).unlink()
        return super(DirectoryConfig, self).execute()
