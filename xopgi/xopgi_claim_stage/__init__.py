# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_claim_stage
# ---------------------------------------------------------------------
# Copyright (c) 2013-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#

from __future__ import absolute_import as _py3_abs_imports

try:
    from openerp.release import version_info as ODOO_VERSION_INFO
    from openerp import models
except ImportError:
    # This is Odoo 10+, but let's be able to get the ODOO_VERSION_INFO
    from odoo.release import version_info as ODOO_VERSION_INFO
    from odoo import models


if ODOO_VERSION_INFO[0] in (8, 9, 10):
    class CrmClaimStage(models.Model):
        _inherit = ['crm.claim.stage', 'base.stage']
        _name = 'crm.claim.stage'
