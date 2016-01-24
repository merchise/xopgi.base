# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.res_config
# ---------------------------------------------------------------------
# Copyright (c) 2014 - 2016 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-01-23

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from openerp import models


class XopgiBoardConfig(models.TransientModel):
    _name = 'xopgi.board.config'
    _inherit = 'res.config.settings'




