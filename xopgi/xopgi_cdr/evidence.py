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

import operator

from xoeuf.odoo import api, exceptions, fields, models, _
from xoeuf.odoo.tools.safe_eval import safe_eval
from xoeuf.osv.orm import CREATE_RELATED

from .util import evaluate, get_free_names

import logging
logger = logging.getLogger(__name__)
del logging


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


class Evidence(models.Model):
    '''The `evidences` are predicates over several `control variables`.

    They test conditions which are *undesired* regarding those variables.
    For example, having defined the 'liquidity' and 'current liabilities'
    variables we may defined a 'low liquidity' evidence via the predicate.

    '''
    _name = 'cdr.evidence'
    _inherits = {'cdr.identifier': 'identifier_id'}

    identifier_id = fields.Many2one(
        'cdr.identifier',
        required=True,
        ondelete='cascade',
        help='Identifier the evidence: name, value, evaluations'
    )

    description = fields.Char(
        translate=True,
        help='Description of the evidence'
    )

    definition = fields.Char(
        required=True,
        help='Python expression combining controls '
             'variables operators and literal values.\n'
             'Eg: var1 - var2 * (var3 or 400) \n'
             'The result must be able to be in an expression like: \n'
             '(result operator operand) resulting a boolean value.'
    )

    operator = fields.Selection(
        [(k, v[0]) for k, v in OPERATORS.items()],
        required=True,
        help='Operator of mathematical language'
    )

    operand = fields.Char(
        required=True,
        help="Python literal.\n"
             "Eg: 1000, False, 0.5, 'Some text'\n"
             "It must be able to be in an expression like: \n"
             "(result operator operand) resulting a boolean value."
    )

    bool_value = fields.Boolean(
        help='Result of your predicate'
    )

    control_vars = fields.Many2many(
        'cdr.control.variable',
        'evidence_control_variable_rel',
        'evidence_id', 'var_id',
        compute='get_vars',
        store=True
    )

    active = fields.Boolean(
        default=True
    )

    cycle = fields.Many2one(
        'cdr.evaluation.cycle',
        help='<CDR_evaluation_cycle>'
    )

    variable = fields.Many2one(
        'cdr.control.variable'
    )

    @api.depends('active', 'definition')
    def get_vars(self):
        '''Get the control variables for an evidence if it has definition and
        is active.

        '''
        control_vars = self.env['cdr.control.variable']
        if self.active and self.definition:
            domain = [('name', 'in', tuple(get_free_names(self.definition)))]
            self.control_vars = control_vars.search(domain)
        else:
            self.control_vars = control_vars

    def get_bool_value(self):
        '''Return a dict with the evidences and the result of your predicate.

        '''
        return {e.name: e.bool_value for e in self}

    def _evaluate(self):
        return evaluate(self.definition, **self.control_vars.get_value())

    def evaluate_bool_expresion(self, definition_result):
        '''Evaluate the predicate's evidence as boolean expression.

        '''
        op_funct = OPERATORS[self.operator][1]
        return bool(op_funct(definition_result, safe_eval(self.operand)))

    @api.constrains('definition', 'operand', 'operator')
    def _check_definition(self):
        '''Evaluate and verify the definition of an evidence.

        '''
        for record in self:
            try:
                # TODO: Compile only
                definition_res = record._evaluate()
                record.evaluate_bool_expresion(definition_res)
            except Exception as e:
                raise exceptions.ValidationError(
                    _("Wrong definition: %s") % e.message
                )

    def evaluate(self, cycle):
        '''Evaluate the evidences in a evaluation cycle.

        '''
        for evidence in self:
            try:
                value = evidence._evaluate()
                bool_value = evidence.evaluate_bool_expresion(value)
            except Exception:
                logger.exception('Error evaluating evidence %s defined as: '
                                 '%s', (evidence.name, evidence.definition))
            else:
                evidence.write(dict(
                    value=repr(value),
                    bool_value=bool_value,
                    cycle=cycle.id,
                    evaluations=[
                        CREATE_RELATED(result=value, cycle=cycle.id),
                        # TODO: WHY? is this set as well
                        CREATE_RELATED(result=bool_value, cycle=cycle.id)
                    ])
                )

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        res = super(Evidence, self).create(vals)
        # evaluate by first time to get init value.
        self.env['cdr.evaluation.cycle'].create(evidences_to_evaluate=res)
        return res
