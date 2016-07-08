# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr.evidence
# ---------------------------------------------------------------------
# Copyright (c) 2016 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-02-13

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from openerp import api, exceptions, fields, models, _
from openerp.tools.safe_eval import safe_eval
import operator
from xoeuf.osv.orm import CREATE_RELATED
from xoutil import logger
from .util import evaluate, get_free_names


OPERATORS = {
    '==': ('equal', operator.eq),
    '!=': ('not equal', operator.ne),
    '>': ('greater than', operator.gt),
    '<': ('lower than', operator.lt),
    '>=': ('lower than or equal', operator.ge),
    '<=': ('lower than or equal', operator.le),
    'is': ('is', operator.is_),
    'not is': ('is not', operator.is_not),
    'in': ('is in', lambda a, b: operator.contains(b, a)),
    'not in': ('is not in', lambda a, b: not operator.contains(b, a)),
    'contain': ('contain', operator.contains),
    'not contain': ('not contain', lambda a, b: not operator.contains(a, b)),
}


def _get_candidates(value):
    if isinstance(value, dict):
        return value.keys()
    elif isinstance(value, (list, set, tuple)):
        return (str(i) for i in range(len(value)))
    else:
        return []


class Evidence(models.Model):
    _name = 'cdr.evidence'
    _inherits = {'cdr.identifier': 'identifier_id'}

    identifier_id = fields.Many2one('cdr.identifier', required=True,
                                    ondelete='cascade')
    description = fields.Char(translate=True)
    definition = fields.Char(
        required=True, help="Python expression combining controls "
                            "variables operators and literal values.\n"
                            "Eg: var1 - var2 * (var3 or 400) \n"
                            "The result must be able to be in an expression like: \n"
                            "(result operator operand) resulting a boolean value.")
    operator = fields.Selection([(k, v[0]) for k, v in OPERATORS.items()],
                                required=True)
    operand = fields.Char(help="Python literal.\n"
                               "Eg: 1000, False, 0.5, 'Some text'\n"
                               "It must be able to be in an expression like: \n"
                               "(result operator operand) resulting a boolean value.",
                          required=True)
    bool_value = fields.Boolean()
    control_vars = fields.Many2many('cdr.control.variable',
                                    'evidence_control_variable_rel',
                                    'evidence_id', 'var_id',
                                    compute='get_vars', store=True)
    active = fields.Boolean(default=True)
    cycle = fields.Many2one('cdr.evaluation.cycle')

    variable = fields.Many2one('cdr.control.variable')
    expression = fields.Char()
    key = fields.Char()
    candidates = fields.Char()
    result = fields.Char()

    def _get_result(self):
        if self.expression:
            res = evaluate(self.expression, **self.variable.get_value())
        else:
            res = ''
        return res

    @api.onchange('variable')
    def onchange_variable(self):
        if self.variable:
            self.expression = self.variable.name
            result = self._get_result()
            self.result = str(result)
            self.candidates = ', '.join(_get_candidates(result))
            self.key = ''
        else:
            self.expression = ''
            self.candidates = ''
            self.result = ''

    @api.onchange('key')
    def onchange_key(self):
        if self.key:
            expression = self.expression
            res = self._get_result()
            try:
                if isinstance(res, dict):
                    res = res.get(self.key)
                    expression = "%s['%s']" % (expression, self.key)
                else:
                    res = res[int(self.key)]
                    expression = "%s[%s]" % (expression, self.key)
                self.key = ''
                self.candidates = ', '.join(_get_candidates(res))
                self.expression = expression
            except:
                res = _('Error')
            self.result = str(res)

    @api.depends('active', 'definition')
    def get_vars(self):
        control_vars = self.env['cdr.control.variable']
        if self.active and self.definition:
            domain = [('name', 'in', tuple(get_free_names(self.definition)))]
            self.control_vars = control_vars.search(domain)
        else:
            self.control_vars = control_vars

    def get_bool_value(self):
        return {e.name: e.bool_value for e in self}

    def _evaluate(self):
        return evaluate(self.definition, **self.control_vars.get_value())

    def evaluate_bool_expresion(self, definition_result):
        op_funct = OPERATORS[self.operator][1]
        return bool(op_funct(definition_result, safe_eval(self.operand)))

    @api.constrains('definition', 'operand', 'operator')
    def check_definition(self):
        try:
            definition_res = self._evaluate()
            self.evaluate_bool_expresion(definition_res)
        except Exception as e:
            raise exceptions.ValidationError(
                _("Wrong definition: %s") % e.message)

    def evaluate(self, cycle):
        for evidence in self:
            try:
                value = evidence._evaluate()
                bool_value = evidence.evaluate_bool_expresion(value)
            except Exception as e:
                logger.exception('Error evaluating evidence %s defined as: '
                                 '%s', (self.name, self.definition))
                logger.exception(e)
            else:
                evidence.write(dict(
                    value=str(value), bool_value=bool_value, cycle=cycle.id,
                    evaluations=[CREATE_RELATED(**dict(value=str(value),
                                                       cycle=cycle.id)),
                                 CREATE_RELATED(**dict(value=str(bool_value),
                                                       cycle=cycle.id))]))

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        res = super(Evidence, self).create(vals)
        # evaluate by first time to get init value.
        self.env['cdr.evaluation.cycle'].create(evidences_to_evaluate=res)
        return res
