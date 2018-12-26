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

from xoeuf import api, fields, models
from xoeuf.odoo import exceptions, _
from xoeuf.osv.orm import CREATE_RELATED
from .util import evaluate

import logging
logger = logging.getLogger(__name__)
del logging


class ControlVariable(models.Model):
    '''The `control variables` define basic mostly numeric evaluations of a
    single basic indicator. For instance, you may define 'the total amount of
    liquidity' you have available.

    '''
    _name = 'cdr.control.variable'
    _inherits = {'cdr.identifier': 'identifier_id'}

    identifier_id = fields.Many2one(
        'cdr.identifier',
        required=True,
        ondelete='cascade',
        help='Identifier the control variable: name, value, evaluations'
    )

    description = fields.Char(
        translate=True,
        help='Description of control variable'
    )

    template = fields.Many2one(
        'cdr.control.variable.template',
        required=True,
        ondelete='restrict',
        help='The template is the key for get a value in a control variable'
    )

    args_need = fields.Boolean(
        related='template.args_need'
    )

    args = fields.Text(
        help="Python dictionary with arguments that template expect."
    )

    @fields.Property
    def arguments(self):
        return evaluate(self.args) if self.args else {}

    evidences = fields.Many2many(
        'cdr.evidence',
        'evidence_control_variable_rel',
        'var_id',
        'evidence_id',
        ondelete='restrict',
        help='Are predicates over several control variables'
    )

    active = fields.Boolean(
        default=True
    )

    cycle = fields.Many2one(
        'cdr.evaluation.cycle',
        help='The control variable are evaluate in evaluation cycle'
    )

    @api.onchange('template', 'template', 'args_need')
    def onchange_template(self):
        '''Take values of
        '''
        if self.template and self.args_need:
            args = [
                "\n\t'%s': " % arg
                for _, arg, _, _ in self.template.definition._formatter_parser()
                if arg
            ] if self.args_need else []
            self.args = "{%s\n}" % ",".join(args)
        else:
            self.args = ""

    def get_value(self):
        '''Get name: value dictionary

        '''
        return {v.name: v.result for v in self}

    def _value(self):
        '''If value: Verify that the value of control variable is evaluated as
        python code else return None.

        '''
        import warnings
        warnings.warn('The _value() method of control variables is '
                      'deprecated.  Use the `result` property.', stacklevel=2)
        return self.result

    @api.requires_singleton
    def _evaluate(self, now=None):
        '''Allow to make python expression for 'args' in the template. The
        field 'args' represent a string of type text.

        '''
        logger.debug('Evaluating %r', self.name)
        from xoeuf.tools import normalize_datetime
        result = self.template.eval(
            normalize_datetime(now or fields.Datetime.now()),
            self.arguments
        )
        logger.debug('Evaluated %r', self.name)
        return result

    @api.constrains('template', 'args')
    def _check_definition(self):
        '''Check the control variable definition.

        '''
        for variable in self:
            try:
                variable.template.compile(variable.arguments)
            except Exception as e:
                raise exceptions.ValidationError(
                    _("Wrong definition: %s") % e.message
                )

    def evaluate(self, cycle):
        '''Evaluate the control variables in a evaluation cycle.

        '''
        if isinstance(cycle, int):
            cycle = self.env['cdr.evaluation.cycle'].browse(cycle)
        import psycopg2
        logger.debug('Start evaluation of %r, cycle: %r', self.mapped('name'), cycle)
        from celery.exceptions import SoftTimeLimitExceeded
        for var in self:
            try:
                value = var._evaluate(cycle.create_date)
            except SoftTimeLimitExceeded:
                raise
            except (psycopg2.InterfaceError, psycopg2.InternalError):
                # This means the cursor is unusable, so there's no point in
                # trying to do anything else with it.
                raise
            except Exception:
                logger.exception(
                    'Error evaluating control variable %s.',
                    var.name
                )
            else:
                var.write(dict(
                    result=value,
                    cycle=cycle.id,
                    evaluations=[CREATE_RELATED(result=value,
                                                cycle=cycle.id)]
                ))
        logger.debug('Done computing variable %r', self.mapped('name'))

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        logger.debug('Creating variable %r', vals)
        res = super(ControlVariable, self).create(vals)
        logger.debug('Created variable %r', res.name)
        # evaluate by first time to get init value.
        self.env['cdr.evaluation.cycle'].create_and_evaluate(variables=res)
        logger.debug('Evaluated variable %r', res.name)
        return res


class ControlVariableTemplate(models.Model):
    '''The template is the key for get a value in a control variable: E.g.

    env['{model}'].browse({instance}).{field} -> One instance field value

    '''
    _name = 'cdr.control.variable.template'

    name = fields.Char(
        translate=True
    )

    reusable = fields.Boolean(
        default=True
    )

    definition = fields.Text(
        help="Python code string. Allow format string arguments in it."
    )

    args_need = fields.Boolean(
        help="Marc if definition need to be formatted."
    )

    eval_mode = fields.Selection(
        [('eval', 'Eval'),
         ('exec', 'Execute')],
        default='eval'
    )

    @api.onchange('reusable')
    def onchange_reusable(self):
        if not self.reusable:
            self.args_need = False

    def compile(self, values):
        '''Compiles the expression with `values`.'''
        source = self.definition
        if self.args_need:
            source = source.format(**values)
        compile(source, '<cdr-variable>', self.eval_mode)  # TODO: safe_compile
        return source

    def eval(self, now, values):
        """Evaluate template definition with given param values.

        :param now: datetime of evaluation cycle start.

        :param values: param values to passe it to str.format() on
                           definition.

        """
        code = self.compile(values)
        return evaluate(code, self.eval_mode, now=now, env=self.env)
