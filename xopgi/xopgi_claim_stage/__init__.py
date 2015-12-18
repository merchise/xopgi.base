# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_claim_stage
# ---------------------------------------------------------------------
# Copyright (c) 2013-2015 Merchise Autrement
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-12-12

from __future__ import absolute_import as _py3_abs_imports

from openerp import fields, models


class CrmClaimStage(models.Model):
    _inherit = ['crm.claim.stage', 'base.stage']
    _name = 'crm.claim.stage'
