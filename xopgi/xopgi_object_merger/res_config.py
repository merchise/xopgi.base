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

from xoeuf import api, fields, models, MAJOR_ODOO_VERSION
from xoeuf.odoo import _
from xoeuf.models.proxy import IrModel

import logging
logger = logging.getLogger(__name__)
del logging


IS_MODEL_ID = '1'
MODEL_FIELD_VALUE_SELECTION = [('0', 'Model Name'), (IS_MODEL_ID, 'Model Id')]


if MAJOR_ODOO_VERSION < 9:
    _NON_TRANSIENT_MODEL_DOMAIN = [('osv_memory', '=', False)]
else:
    _NON_TRANSIENT_MODEL_DOMAIN = [('transient', '=', False)]


class ir_model(models.Model):
    _inherit = 'ir.model'

    _sql_constraints = [
        ('positive_merge_limit', 'check (merge_limit >= 0)',
         'The limit quantity of objects to allow merge at one time must be '
         'positive number!'),
    ]

    object_merger_model = fields.Boolean(
        'Object Merger',
        help=('If checked, by default the Object Merger configuration will '
              'get this module in the list')
    )
    merge_limit = fields.Integer(
        'Merge Limit',
        default=0,
        help='Limit quantity of objects to allow merge at one time.'
    )
    field_merge_way_ids = fields.One2many(
        'field.merge.way.rel',
        'model',
        string='Specific Merge Ways',
        help='Specify how to merge the fields'
    )

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        if (view_type == 'form' and self._context.get('object_merger_settings', False)):
            _, view_id = self.env['ir.model.data'].get_object_reference(
                'xopgi_object_merger',
                'view_ir_model_merge_form'
            )
        res = super(ir_model, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu
        )
        return res

    @api.requires_singleton
    def _merge(self, sources, target):
        if self.field_merge_way_ids:
            values = self.field_merge_way_ids.meld(sources, target)
        else:
            values = {}
        if values:
            target.write(values)


class InformalReference(models.Model):
    _name = 'informal.reference'

    table_name = fields.Char(
        'Table Name',
        size=128,
        required=True,
        help='Name of DB table where informal reference are.'
    )
    id_field_name = fields.Char(
        'Id Field Name',
        size=128,
        required=True,
        default='res_id',
        help='Name of field where destination id are saved.'
    )
    model_field_name = fields.Char(
        'Model Field Name',
        size=128,
        required=True,
        default='res_model',
        help='Name of field where destination model are saved.'
    )
    model_field_value = fields.Selection(
        MODEL_FIELD_VALUE_SELECTION,
        'Model Field Value',
        required=True,
        default='0',
        help='How save destination model reference.'
    )


class object_merger_settings(models.Model):
    _name = 'object.merger.settings'
    _inherit = 'res.config.settings'

    def _get_default_object_merger_models(self):
        return IrModel.sudo().search([('object_merger_model', '=', True)])

    models_ids = fields.Many2many(
        'ir.model',
        'object_merger_settings_model_rel',
        'object_merger_id',
        'model_id',
        string='Models',
        domain=_NON_TRANSIENT_MODEL_DOMAIN,
        context={'object_merger_settings': True},
        default=_get_default_object_merger_models
    )

    informal_reference_ids = fields.Many2many(
        'informal.reference',
        'object_merger_informal_reference_rel',
        'object_merger_id',
        'informal_reference_id',
        'Informal References',
        help='Know cases of pair of field represented a '
             'reference to an specific object from '
             'especific model.',
        default=lambda s: s.env['informal.reference'].search([])
    )

    @api.multi
    def update_field(self):
        model_obj = self.env['ir.model']
        action_obj = self.env['ir.actions.act_window']
        value_obj = self.env['ir.values']
        field_obj = self.env['ir.model.fields']
        template_action = self.sudo().env.ref(
            'xopgi_object_merger.act_merge_template',
            raise_if_not_found=False
        )
        if not self:
            return False
        # Unlink Previous Actions
        unlink_records = action_obj.search([
            ('res_model', '=', 'object.merger'),
            ('id', '!=', template_action.id)
        ])
        for unlink_id in unlink_records:
            unlink_id.unlink()
            un_val = value_obj.search([
                ('value', '=', "ir.actions.act_window," + str(unlink_id.id))])
            un_val.unlink()
        # Put all models which were selected before back to not an object_merger
        model_not_merge = model_obj.search([('id', 'not in', self.models_ids.ids),
                                            ('object_merger_model', '=', True)])
        model_not_merge.write({'object_merger_model': False})
        # Put all models which are selected to be an object_merger
        self.models_ids.write({'object_merger_model': True})
        object_merger = self.models_ids.search([
            ('model', '=', 'object.merger')], limit=1
        )
        for model in self.models_ids:
            field_name = 'x_' + model.model.replace('.', '_') + '_id'
            name = "Merge"
            default = {
                'src_model': model.model,
                'context': {'field_to_read': field_name}
            }
            temp_acc = template_action.copy(default=default)
            value_obj.create({
                'name': name,
                'model': model.model,
                'key2': 'client_action_multi',
                'value': "ir.actions.act_window," + str(temp_acc.id)
            })
            found = field_obj.search(
                [('name', '=', field_name), ('model', '=', 'object.merger')]
            )
            if not found:
                field_data = {
                    'model': 'object.merger',
                    'model_id': object_merger.id,
                    'name': field_name,
                    'relation': model.model,
                    'field_description': _('To keep'),
                    'state': 'manual',
                    'ttype': 'many2one',
                }
                field_obj.sudo().create(field_data)
        return True

    @api.multi
    def install(self):
        self.update_field()
        return {'type': 'ir.actions.client', 'tag': 'reload', }


class FieldMergeWay(models.Model):
    _name = 'field.merge.way'

    name = fields.Char(required=True, translate=True)
    code = fields.Selection(
        [('add', 'Add both fields'),
         ('min', 'Keep the minimal'),
         ('max', 'Keep the maximal'),
         ('average', 'Find the average'),
         ('sum', 'Find the sum')],
        required=True,
    )

    _sql_constraints = [
        ('name_unique', 'unique (name)', 'Strategy must be unique!')]

    def apply(self, sources, target, field):
        method = getattr(self, 'apply_' + self.code, None)
        try:
            if method:
                return method(sources, target, field)
            else:
                return None
        except:  # TODO: Which exceptions
            logger.exception(
                'An error happened trying to execute the Specific Merge '
                'Way python code for Model: %s, Field: %s, '
                'Target id: %s and Sources ids: %s',
                field.model, field.field_description, target.id,
                sources.ids
            )

    def apply_add(self, sources, target, field):
        result = getattr(target, field.name, None)
        if field.ttype == 'char':
            union = ' '
        elif field.ttype == 'text':
            union = ' '
        else:
            union = False
        for obj in sources:
            temp = getattr(obj, field.name, None)
            if result and temp:
                result += union + temp if union else temp
            elif not result:
                result = temp
        return result

    def apply_average(self, sources, target, field):
        result = getattr(target, field.name, 0)
        count = 1 if result not in [False, None] else 0
        for obj in sources:
            temp = getattr(obj, field.name, None)
            if not any(var in [False, None] for var in (result, temp)):
                result += temp
                count += 1
        return result / count if result and count else 0

    def apply_sum(self, sources, target, field):
        return self._reduce(
            operator.add,
            sources,
            target,
            field,
            0
        )

    def apply_max(self, sources, target, field):
        from xoutil.infinity import Infinity
        return self._reduce(
            max,
            sources,
            target,
            field,
            -Infinity
        )

    def apply_min(self, sources, target, field):
        from xoutil.infinity import Infinity
        return self._reduce(
            min,
            sources,
            target,
            field,
            -Infinity
        )

    def _reduce(self, f, sources, target, field, initial):
        result = getattr(target, field.name, initial)
        for temp in sources.mapped(field.name):
            result = f(result, temp)
        return result


class FieldMergeWayRel(models.Model):
    _name = 'field.merge.way.rel'

    name = fields.Many2one('ir.model.fields', required=True)
    merge_way = fields.Many2one('field.merge.way', required=True)
    model = fields.Many2one('ir.model', required=True)

    @api.multi
    def meld(self, sources, target):
        res = {}
        for item in self:
            val = item.merge_way.apply(sources, target, item.name)
            if val is not None:
                res[item.name.name] = val
        return res
