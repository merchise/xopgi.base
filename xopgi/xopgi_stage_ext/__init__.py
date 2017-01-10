# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_stage_ext
# ---------------------------------------------------------------------
# Copyright (c) 2013-2015 Merchise Autrement [~º/~]
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-12-12

from __future__ import absolute_import as _py3_abs_imports

try:
    from openerp.release import version_info as ODOO_VERSION_INFO
    from openerp import fields, models
except ImportError:
    # This is Odoo 10+, but let's be able to get the ODOO_VERSION_INFO
    from odoo.release import version_info as ODOO_VERSION_INFO
    from odoo import fields, models


if (8, 0) <= ODOO_VERSION_INFO < (9, 0):
    class BaseStage(models.AbstractModel):
        _name = 'base.stage'

        flow_start = fields.Boolean()
        flow_stop = fields.Boolean()
