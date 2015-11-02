# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2013 OpenERP s.a. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, models
from itertools import groupby


class XopgiBoard(models.Model):
    _name = 'xopgi.board'
    _description = "Board"

    @api.model
    def get_board_widgets(self):
        lst = self.get_data()
        lst.sort(key=lambda x: (x.get('category', 'z'),
                                x.get('priority', 1000),
                                x.get('string', '')))
        result = [list(itr) for k, itr in
                  groupby(lst, lambda x: x.get('category', x))]
        return result

    @api.model
    def get_data(self):
        """Override this method to add new board widget.
        :return: list of dict like {
            'template': 'template_x',  # Qweb template name to render.
            'string': 'widget x',  # Title of widget.
            'priority': 1,  # Priority to putting on board.
            'category': 'sale', # Each category will be a row.
            'xml_templa': ''' # String of qweb template to add and render.
                <templates>
                  <t t-name="pruebaaa">
                    <div t-esc="text"/>
                  </t>
                </templates>
            '''
            #  Any additional data E.g: values to show on board.
        }
        """
        return []

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
