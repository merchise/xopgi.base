# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.board_widget
# ---------------------------------------------------------------------
# Copyright (c) 2014, 2015 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2015-11-12

from openerp import api, fields, models
from openerp.tools.safe_eval import safe_eval
from xoutil import logger


class XopgiBoardWidget(models.Model):
    _name = 'xopgi.board.widget'
    _description = "Board Widget"

    _order = 'category, priority, name'

    name = fields.Char(translate=True)
    priority = fields.Integer(default=1000)
    category = fields.Many2one('ir.module.category')
    template_name = fields.Char(required=True)
    xml_template = fields.Text(translate=True)
    python_code = fields.Text()
    job_positions = fields.Many2many('hr.job')
    users = fields.Many2many('res.users', compute=lambda *a: False,
                             search='_search_by_user')

    @api.multi
    def name_get(self):
        return [(item.id, item.name or item.template_name) for item in self]

    def _search_by_user(self, operator, operand):
        """ This is made to allow create an ir.rule based on logged user jobs.

        """
        if not self._context.get('show_all', False):
            jobs = self.env['hr.job'].search(
                [('employee_ids.user_id', operator, operand)])
            return [('job_positions', 'in', jobs.ids)]
        else:
            return []

    def get_widgets_dict(self):
        widgets = self.search_read(fields=[
            'name', 'category', 'template_name', 'xml_template',
            'python_code'])
        logger.debug(
            'Widgets to show %r' % [w['name'] for w in widgets])
        for widget in widgets:
            self._eval_python_code(widget)
        return widgets

    def _eval_python_code(self, widget):
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
                             'code for \'%s\' board widget, python code: %s'
                             % (name, python_code))
        widget.update(local_dict.get('result', {}))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
