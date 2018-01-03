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

from xoeuf import api, models, SUPERUSER_ID
from xoeuf.models import get_modelname
from xoeuf.models.proxy import IrUiMenu as ir_ui_menu, XopgiBoardWidgetRel


class Menu(models.Model):
    _inherit = get_modelname(ir_ui_menu)

    @api.model
    def get_user_roots(self):
        preview_menu = None
        if self._uid != SUPERUSER_ID:
            widget_models = XopgiBoardWidgetRel.get_widget_capable_models()
            # if active user has no widget to see on preview.
            if not any(m.get_user_widgets() for m in widget_models):
                preview_menu = self.env.ref('xopgi_board.menu_board_my_dash',
                                            raise_if_not_found=False)
        return super(Menu, self.with_context(exclude_menu_items=preview_menu)).get_user_roots()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        from xoeuf.osv import expression as expr
        exclude = self.env.context.get('exclude_menu_items')
        if exclude:
            args = expr.AND([args, [('id', 'not in', exclude.ids)]])
        return super(Menu, self).search(
            args,
            offset=offset,
            limit=limit,
            order=order,
            count=count
        )
