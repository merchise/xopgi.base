# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.ir_ui_menu
# ---------------------------------------------------------------------
# Copyright (c) 2016-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-07-07

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from openerp import api, models, SUPERUSER_ID
from openerp.addons.base.ir.ir_ui_menu import ir_ui_menu
from xoeuf.osv.orm import get_modelname
from .board_widget import WIDGET_REL_MODEL_NAME


class IrUiMenu(models.Model):
    _inherit = get_modelname(ir_ui_menu)

    @api.model
    def get_user_roots(self):
        result = super(IrUiMenu, self).get_user_roots()
        if self._uid != SUPERUSER_ID:
            widget_models = self.env[
                WIDGET_REL_MODEL_NAME].get_widget_capable_models()
            # if active user has no widget to see on preview.
            if not any(m.get_user_widgets() for m in widget_models):
                preview_menu = self.env.ref('xopgi_board.menu_board_my_dash',
                                            raise_if_not_found=False)
                if preview_menu:
                    # exclude preview menu without change order.
                    result = [i for i in result if i != preview_menu.id]
        return result
