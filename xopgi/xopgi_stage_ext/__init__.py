# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_stage_ext
# ---------------------------------------------------------------------
# Copyright (c) 2013-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#

from __future__ import absolute_import as _py3_abs_imports

from xoeuf import ODOO_VERSION_INFO
from xoeuf import models, fields


if 8 <= ODOO_VERSION_INFO[0] < 11:
    class BaseStage(models.AbstractModel):
        _name = 'base.stage'

        flow_start = fields.Boolean()
        flow_stop = fields.Boolean()
