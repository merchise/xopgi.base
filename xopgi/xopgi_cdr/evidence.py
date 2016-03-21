# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr.evidence
# ---------------------------------------------------------------------
# Copyright (c) 2016 Merchise Autrement and Contributors
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
from xoutil import logger
from .util import evaluate, get_free_names


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
    operator = fields.Char(help="Python comparative operator.\n"
                                "Eg: >, >=, is, in, not in\n"
                                "It be apply between result of definition evaluation and operand.")
    operand = fields.Char(help="Python literal.\n"
                               "Eg: 1000, False, 0.5, 'Some text'\n"
                               "It must be able to be in an expression like: \n"
                               "(result operator operand) resulting a boolean value.")
    value = fields.Char()
    bool_value = fields.Boolean()
    control_vars = fields.Many2many('cdr.control.variable',
                                    'evidence_control_variable_rel',
                                    'evidence_id', 'var_id',
                                    compute='get_vars', store=True)
    active = fields.Boolean(default=True)
    cycle = fields.Many2one('cdr.evaluation.cycle')

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
        return evaluate(self.env, self.definition,
                        **self.control_vars.get_value())

    def evaluate_bool_expresion(self, definition_result):
        return bool(safe_eval(
            "%s %s %s" % (definition_result, self.operand, self.operator)))

    @api.constrains('definition', 'operand', 'operator')
    def check_definition(self):
        try:
            definition_res = self._evaluate()
            self.evaluate_bool_expresion(definition_res)
        except Exception, e:
            raise exceptions.ValidationError(
                _("Wrong definition: %s") % e.message)

    def evaluate(self, cycle):
        for evidence in self:
            try:
                value = evidence._evaluate()
                bool_value = evidence.evaluate_bool_expresion(value)
            except Exception, e:
                logger.exception('Error evaluating evidence %s defined as: '
                                 '%s', (self.name, self.definition))
                logger.exception(e)
            else:
                evidence.write(dict(
                    value=str(value), bool_value=bool_value, cycle=cycle.id))
