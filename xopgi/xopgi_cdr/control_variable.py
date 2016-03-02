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
    _inherit = {'cdr.identifier': 'identifier_id'}

    identifier_id = fields.Many2one('cdr.identifier',
                                    required=True, ondelete='cascade')
    description = fields.Char(translate=True)
    template = fields.Many2one('cdr.control.variable.template', required=True)
    args_need = fields.Boolean(related='template.args_need')
    args = fields.Text(
        help="Python dictionary with arguments that template expect.")
    value = fields.Char()
    evidences = fields.Many2many('cdr.evidence',
                                 'evidence_control_variable_rel', 'var_id',
                                 'evidence_id', ondelete='restrict')
    active = fields.Boolean(default=True)
    cycle = fields.Many2one('cdr.evaluation.cycle')

    @api.onchange('template', 'template.definition', 'args_need')
    def onchange_template(self):
        args = [
            "\n\t'%s': " % arg
            for _, arg, _, _ in self.template.definition._formatter_parser()
            if arg
        ] if self.args_need else []
        self.args = "{\n%s\n}" % ",".join(args)

    def get_value(self):
        '''Get name: value dictionary

        '''
        return {v.name: safe_eval(v.value) if v.value else None for v in self}

    def _evaluate(self):
        return self.template.eval(**safe_eval(self.args)
                                  if self.template.args_need else {})

    @api.constrains('template', 'template.definition', 'args')
    def check_definition(self):
        try:
            self._evaluate()
        except Exception, e:
            raise exceptions.ValidationError(_("Wrong definition: %s") %
                                             e.message)

    def evaluate(self, cycle):
        for var in self:
            try:
                value = var._evaluate()
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


class ControlVariableTemplate(models.Model):
    _name = 'cdr.control.variable.template'

    name = fields.Char(translate=True)
    definition = fields.Text(help="Python code string. Allow format string "
                                  "arguments in it.")
    args_need = fields.Boolean(help="Marc if definition need to be formatted.")
    eval_mode = fields.Selection([('eval', 'Eval'), ('exec', 'Execute')],
                                 default='eval')

    def eval(self, **kwargs):
        # TODO: exception treatment

        code = self.definition
        if self.args_need:
            try:
                code = code.format(**kwargs)
            except Exception, e:
                logger.exception(
                    'Error formatting control variable template '
                    '%s: %s with %s params.', (self.name, self.definition,
                                               str(kwargs)))
                logger.exception(e)
                code = None
        if code:
            return evaluate(self.env, code, self.eval_mode)
        return None
