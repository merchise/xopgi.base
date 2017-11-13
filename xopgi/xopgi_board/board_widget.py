# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.board_widget
# ---------------------------------------------------------------------
# Copyright (c) 2014-2017 Merchise Autrement [~º/~] and Contributors
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
import operator
import itertools
from xoeuf import api, fields, models
from xoeuf.odoo.tools.safe_eval import safe_eval
from xoeuf.tools import normalize_datetime


WIDGET_MODEL_NAME = 'xopgi.board.widget'
WIDGET_REL_MODEL_NAME = 'xopgi.board.widget.rel'


class XopgiBoardWidget(models.Model):
    _name = WIDGET_MODEL_NAME
    _description = "Board Widget"

    _order = 'category, name'

    name = fields.Char(translate=True)
    category = fields.Many2one('ir.module.category')
    template_name = fields.Char(required=True)
    xml_template = fields.Text(translate=True)
    python_code = fields.Text()

    @api.multi
    def name_get(self):
        '''Returns a list with id, name of widgets or name's template

        '''
        return [(item.id, item.name or item.template_name) for item in self]

    def get_widgets_dict(self):
        '''Returns a dictionary list that represents the widgets that the user
        has access to.

        '''
        widgets = self.env[WIDGET_REL_MODEL_NAME].get_widgets()
        logger.debug(
            'Widgets to show %r' % [w['name'] for w in widgets])
        today = normalize_datetime(fields.Date.today(self))
        for widget in widgets:
            self._eval_python_code(widget, today)
        return widgets

    def _eval_python_code(self, widget, today):
        '''Evaluate the python code of a widget

        '''
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
        except ValueError:
            logger.exception('An error happen trying to execute the Python '
                             'code for \'%s\' board widget, python code: %s',
                             name, python_code)
        widget.update(local_dict.get('result', {}))


class XopgiBoardWidgetRel(models.AbstractModel):
    _name = WIDGET_REL_MODEL_NAME
    _order = 'priority'

    widget = fields.Many2one(WIDGET_MODEL_NAME, delegate=True,
                             required=True, ondelete='cascade')
    priority = fields.Integer(default=1000)

    def get_widgets(self):
        """ Get all widget dicts for uid and sorts them by priority.

        """
        models = self.get_widget_capable_models()
        widgets = sorted(itertools.chain(*[list(model.get_user_widgets())
                                           for model in models]),
                         key=operator.attrgetter('priority'))
        result = []
        # Adding missing widget
        for widget in widgets:
            widget.get_set_widgets(result)
        return result

    def get_user_widgets(self):
        """ It must be implemented on extended models.

        Should return a recordset of user's corresponding widgets.

        """
        raise NotImplementedError()

    def get_widget_capable_models(self):
        """ Get a list of models instances that have `get_user_widgets` item

        """
        result = []
        for model in self.env.registry.values():
            if hasattr(model, "get_user_widgets"):
                if model._name != WIDGET_REL_MODEL_NAME:
                    result.append(self.env[model._name])
        return result

    def get_set_widgets(self, result):
        """ Update in-place result adding missing widgets.

        """
        for widget in self.read(fields=['name', 'category', 'template_name',
                                        'xml_template', 'python_code']):
            widget.pop('id', None)
            if widget not in result:
                result.append(widget)
