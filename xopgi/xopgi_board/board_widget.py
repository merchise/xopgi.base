# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.board_widget
# ---------------------------------------------------------------------
# Copyright (c) 2014, 2015 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2015-11-12

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoutil import logger

from openerp import api, fields, models
from openerp.tools.safe_eval import safe_eval

from xoeuf.tools import normalize_datetime


class XopgiBoardWidget(models.Model):
    _name = 'xopgi.board.widget'
    _description = "Board Widget"

    _order = 'category, name'

    name = fields.Char(translate=True)
    category = fields.Many2one('ir.module.category')
    template_name = fields.Char(required=True)
    xml_template = fields.Text(translate=True)
    python_code = fields.Text()
    job_positions = fields.Many2many('hr.job')

    @api.multi
    def name_get(self):
        return [(item.id, item.name or item.template_name) for item in self]

    def get_widgets_dict(self):
        widgets = self.env['hr.job.widget'].get_user_widgets()
        logger.debug(
            'Widgets to show %r' % [w['name'] for w in widgets])
        today = normalize_datetime(fields.Date.today(self))
        for widget in widgets:
            self._eval_python_code(widget, today)
        return widgets

    def _eval_python_code(self, widget, today):
        python_code = widget.get('python_code', '')
        if not python_code:
            return
        name = widget.get('name', '')
        env = self.env
        local_dict = locals()
        local_dict.update(globals().get('__builtins__', {}))
        try:
            logger.debug('Starting evaluation of Python code for widget %s' %
                         name)
            safe_eval(python_code, local_dict, mode='exec', nocopy=True)
            logger.debug('Python code for widget %s evaluated sussefully.' %
                         name)
        except:
            logger.exception('An error happen trying to execute the Python '
                             'code for \'%s\' board widget, python code: %s',
                             name, python_code)
        widget.update(local_dict.get('result', {}))
