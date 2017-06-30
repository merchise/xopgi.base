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

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoeuf import ODOO_VERSION_INFO
from xoeuf import models


if ODOO_VERSION_INFO[0] in (8, 9, 10):
    class CrmClaimStage(models.Model):
        _inherit = ['crm.claim.stage', 'base.stage']
        _name = 'crm.claim.stage'
