# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.board
# ---------------------------------------------------------------------
# Copyright (c) 2014, 2015 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2015-10-29

from openerp import api, models
from itertools import groupby


class XopgiBoard(models.Model):
    _name = 'xopgi.board'
    _description = "Board"

    @api.model
    def get_board_widgets(self):
        lst = self.get_data()
        result = [list(itr) for k, itr in
                  groupby(lst, lambda x: x.get('category', x))]
        return result

    def get_data(self):
        return self.env['xopgi.board.widget'].get_widgets_dict()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
