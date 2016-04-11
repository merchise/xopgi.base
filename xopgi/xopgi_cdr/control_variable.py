# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr.control_variable
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
from xoeuf.osv.orm import CREATE_RELATED
from xoutil import logger
from .util import evaluate


def check_identifier(identifier):
    """ check identifier is a correct python identifier and not shadow a
    global builtin.

    """
    if not identifier[0].isalpha() and identifier[0] != '_':
        return False
    if identifier in globals().get('__builtins__', {}):
        return False
    if len(identifier) > 1:
        for char in identifier[1:]:
            if not char.isalnum() and char != '_':
                return False
    return True


class CDRIdentifier(models.Model):
    _name = 'cdr.identifier'

    name = fields.Char(required=True,
                       help="Must be a available python identifier.\n"
                            "Just letters, digit (never in first position) "
                            "and underscore are allowed.")
    value = fields.Char()
    evaluations = fields.One2many('cdr.history', 'identifier')
    _sql_constraints = [
        ('identifier_name_unique', 'unique(name)', 'Name already exists')
    ]

    @api.constrains('name')
    def check_name(self):
        if not check_identifier(self.name):
            raise exceptions.ValidationError(
                _("Name must be a available python identifier"))


class ControlVariable(models.Model):
    _name = 'cdr.control.variable'
    _inherits = {'cdr.identifier': 'identifier_id'}

    identifier_id = fields.Many2one('cdr.identifier',
                                    required=True, ondelete='cascade')
    description = fields.Char(translate=True)
    template = fields.Many2one('cdr.control.variable.template',
                               required=True, ondelete='restrict')
    args_need = fields.Boolean(related='template.args_need')
    args = fields.Text(
        help="Python dictionary with arguments that template expect.")
    evidences = fields.Many2many('cdr.evidence',
                                 'evidence_control_variable_rel', 'var_id',
                                 'evidence_id', ondelete='restrict')
    active = fields.Boolean(default=True)
    cycle = fields.Many2one('cdr.evaluation.cycle')

    @api.onchange('template', 'template', 'args_need')
    def onchange_template(self):
        if self.template and self.args_need:
            args = [
                "\n\t'%s': " % arg
                for _, arg, _, _ in self.template.definition._formatter_parser()
                if arg
            ] if self.args_need else []
            self.args = "{\n%s\n}" % ",".join(args)
        else:
            self.args = ""

    def get_value(self):
        '''Get name: value dictionary

        '''
        return {v.name: v._value() for v in self}

    def _value(self):
        return safe_eval(self.value) if self.value else None

    def _evaluate(self, now=None):
        return self.template.eval(now or fields.Datetime.now(),
                                  self.args if self.template.args_need else {})

    @api.constrains('template', 'args')
    def check_definition(self):
        try:
            self._evaluate()
        except Exception, e:
            raise exceptions.ValidationError(_("Wrong definition: %s") %
                                             e.message)

    def evaluate(self, cycle):
        for var in self:
            try:
                value = var._evaluate(cycle.create_date)
            except Exception, e:
                logger.exception('Error evaluating control variable '
                                 '%s.', (self.name,))
                logger.exception(e)
            else:
                var.write(dict(
                    value=str(value),
                    cycle=cycle.id,
                    evaluations=[CREATE_RELATED(
                        **dict(value=str(value), cycle=cycle.id))]))

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        res = super(ControlVariable, self).create(vals)
        self.env['cdr.evaluation.cycle'].create(vars_to_evaluate=res)
        return res


class ControlVariableTemplate(models.Model):
    _name = 'cdr.control.variable.template'

    name = fields.Char(translate=True)
    reusable = fields.Boolean(default=True)
    definition = fields.Text(help="Python code string. Allow format string "
                                  "arguments in it.")
    args_need = fields.Boolean(help="Marc if definition need to be formatted.")
    eval_mode = fields.Selection([('eval', 'Eval'), ('exec', 'Execute')],
                                 default='eval')

    @api.onchange('reusable')
    def onchange_reusable(self):
        if not self.reusable:
            self.args_need = False

    def eval(self, now, kwargs_str):
        # TODO: exception treatment

        code = self.definition
        if self.args_need:
            try:
                kwargs = evaluate(kwargs_str)
                code = code.format(**kwargs)
            except Exception, e:
                logger.exception(
                    'Error formatting control variable template '
                    '%s: %s with %s params.', (self.name, self.definition,
                                               str(kwargs)))
                logger.exception(e)
                code = None
        if code:
            return evaluate(code, self.eval_mode, now=now, env=self.env)
        return None
