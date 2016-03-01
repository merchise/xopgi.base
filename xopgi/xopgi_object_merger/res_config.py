#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_object_merger.res_config
# --------------------------------------------------------------------------
# Copyright (c) 2014-2016 Merchise Autrement and Contributors
# All rights reserved.
#
# Author: Merchise Autrement
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoutil import logger

from openerp.osv import fields, osv, orm
from openerp.tools.safe_eval import safe_eval
from openerp.tools.translate import _
from operator import gt, lt
from openerp import api, fields as new_api_fields, models, SUPERUSER_ID

from xoeuf.osv.orm import LINK_RELATED

IS_MODEL_ID = '1'
MODEL_FIELD_VALUE_SELECTION = [('0', 'Model Name'), (IS_MODEL_ID, 'Model Id')]


class ir_model(orm.Model):
    _inherit = 'ir.model'

    _columns = {
        'object_merger_model':
            fields.boolean('Object Merger', help='If checked, by default '
                                                 'the Object Merger '
                                                 'configuration will get this'
                                                 ' module in the list'),
        'merge_cyclic':
            fields.boolean(string='Merge cyclic relations', type='boolean'),
        'merge_limit':
            fields.integer('Merge Limit', help='Limit quantity of objects to '
                                               'allow merge at one time.'),
        'field_merge_way_ids':
            fields.one2many('field.merge.way.rel', 'model',
                            string='Specific Merge Ways'),
        'general_merge_way': fields.text('General Merge Way')
    }

    _defaults = {'merge_limit': 0}

    _sql_constraints = [
        ('positive_merge_limit', 'check ( merge_limit >= 0 )',
         'The limit quantity of objects to allow merge at one time must be '
         'positive number!'),
    ]

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        if (view_type == 'form' and
                (context or {}).get('object_merger_settings', False)):
            _, view_id = self.pool.get('ir.model.data').get_object_reference(
                cr,
                uid,
                'xopgi_object_merger',
                'view_ir_model_merge_form'
            )
        res = super(ir_model, self).fields_view_get(
            cr,
            uid,
            view_id=view_id,
            view_type=view_type,
            context=context,
            toolbar=toolbar,
            submenu=submenu
        )
        return res

    @api.one
    @api.multi
    def merge(self, dst_id, src_ids):
        dst_obj = self.env[self.model].browse(dst_id)
        src_objs = self.env[self.model].browse(src_ids)
        values = (self.field_merge_way_ids.merge(dst_obj, src_objs)
                  if bool(self.field_merge_way_ids) else {})
        local_dict = locals()
        local_dict.update(globals().get('__builtins__', {}))
        if self.general_merge_way:
            try:
                safe_eval(self.general_merge_way, local_dict, mode='exec',
                          nocopy=True)
                values.update(local_dict.get('result', {}))
            except:
                logger.exception('An error happen trying to execute the General '
                                 'Merge Way python code. for Model: %s, '
                                 'Destination id: %s and Source ids: %s' %
                                 (self.model, str(dst_id), str(src_ids)))
        try:
            if values:
                dst_obj.write(values)
        except:
            logger.exception(
                'An error happen updating result object with: \n%s \n'
                'For Model: %s, Destination id: %s and Source ids: %s' %
                (str(values), self.model, str(dst_id), str(src_ids)))


class InformalReference(orm.Model):
    _name = 'informal.reference'

    _columns = {
        'table_name':
            fields.char('Table Name', size=128, required=True,
                        help='Name of DB table where informal reference are.'),
        'id_field_name':
            fields.char('Id Field Name', size=128, required=True,
                        help='Name of field where destination id are saved.'),
        'model_field_name':
            fields.char('Model Field Name', size=128, required=True,
                        help='Name of field where destination model are saved.'),
        'model_field_value':
            fields.selection(MODEL_FIELD_VALUE_SELECTION, 'Model Field Value',
                             required=True, help='How save destination '
                                                 'model reference.'),
    }

    _defaults = {
        'id_field_name': 'res_id',
        'model_field_name': 'res_model',
        'model_field_value': '0'
    }

    def get_all(self, cr, uid):
        return self.browse(cr, uid, self.get_all_ids(cr, uid))

    def get_all_ids(self, cr, uid):
        return self.search(cr, uid, [])

    def unlink_rest(self, cr, uid, no_unlink_ids):
        unlink_ids = self.search(cr, uid, [('id', 'not in', no_unlink_ids)])
        self.unlink(cr, uid, unlink_ids)


class object_merger_settings(osv.osv_memory):
    _name = 'object.merger.settings'
    _inherit = 'res.config.settings'

    _columns = {
        'models_ids':
            fields.many2many(
                'ir.model', 'object_merger_settings_model_rel',
                'object_merger_id', 'model_id', 'Models',
                domain=[('osv_memory', '=', False)],
                context={'object_merger_settings': True}
            ),
        'informal_reference_ids':
            fields.many2many('informal.reference',
                             'object_merger_informal_reference_rel',
                             'object_merger_id', 'informal_reference_id',
                             'Informal References',
                             help='Know cases of pair of field represented a '
                                  'reference to an specific object from '
                                  'especific model.'),
    }

    def _get_default_object_merger_models(self, cr, uid, context=None):
        return self.pool.get('ir.model').search(cr, uid, [
            ('object_merger_model', '=', True)], context=context)

    _defaults = {
        'models_ids': _get_default_object_merger_models,
        'informal_reference_ids':
            lambda s, c, u, cxt: s.pool['informal.reference'].get_all_ids(
                c, u)
    }

    def update_field(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        model_ids = []
        model_obj = self.pool.get('ir.model')
        action_obj = self.pool.get('ir.actions.act_window')
        value_obj = self.pool.get('ir.values')
        field_obj = self.pool.get('ir.model.fields')
        rol = self.pool['ir.model.data'].xmlid_to_res_id(
            cr, SUPERUSER_ID, 'xopgi_object_merger.group_merger_manager',
            raise_if_not_found=False)
        if not vals or not vals.get('models_ids', False):
            return False
        elif vals.get('models_ids') or model_ids[0][2]:
            model_ids = vals.get('models_ids')
            if isinstance(model_ids[0], (list)):
                model_ids = model_ids[0][2]
        # Unlink Previous Actions
        unlink_ids = action_obj.search(cr, uid,
                                       [('res_model', '=', 'object.merger')],
                                       context=context)
        for unlink_id in unlink_ids:
            action_obj.unlink(cr, uid, unlink_id)
            un_val_ids = value_obj.search(
                cr, uid,
                [('value', '=', "ir.actions.act_window," + str(unlink_id))],
                context=context
            )
            value_obj.unlink(cr, uid, un_val_ids, context=context)
        # Put all models which were selected before back to not an object_merger
        model_not_merge_ids = model_obj.search(
            cr,
            uid,
            [('id', 'not in', model_ids), ('object_merger_model', '=', True)],
            context=context
        )
        model_obj.write(cr, uid, model_not_merge_ids,
                        {'object_merger_model': False}, context=context)
        # Put all models which are selected to be an object_merger
        model_obj.write(cr, uid, model_ids, {'object_merger_model': True},
                        context=context)
        object_merger_ids = model_obj.search(cr, uid,
                                             [('model', '=', 'object.merger')],
                                             context=context)
        read_datas = model_obj.read(cr, uid, model_ids,
                                    ['model', 'name', 'object_merger_model'],
                                    context=context)
        for model in read_datas:
            field_name = 'x_' + model['model'].replace('.', '_') + '_id'
            act_id = action_obj.create(cr, uid, {
                'name': "%s " % model['name'] + _("Merger"),
                'type': 'ir.actions.act_window', 'res_model': 'object.merger',
                'src_model': model['model'], 'view_type': 'form',
                'groups_id': [LINK_RELATED(rol)],
                'context': "{'field_to_read':'%s'}" % field_name,
                'view_mode': 'form', 'target': 'new', }, context=context)
            value_obj.create(
                cr,
                uid,
                {'name': "%s " % model['name'] + _("Merger"),
                 'model': model['model'], 'key2': 'client_action_multi',
                 'value': "ir.actions.act_window," + str(act_id), },
                context=context
            )
            field_name = 'x_' + model['model'].replace('.', '_') + '_id'
            if not field_obj.search(cr, uid, [('name', '=', field_name), (
                    'model', '=', 'object.merger')], context=context):
                field_data = {
                    'model': 'object.merger',
                    'model_id': object_merger_ids and object_merger_ids[0] or False,
                    'name': field_name,
                    'relation': model['model'],
                    'field_description': "%s " % model['name'] + _('To keep'),
                    'state': 'manual',
                    'ttype': 'many2one',
                }
                field_obj.create(cr, SUPERUSER_ID, field_data, context=context)
        return True

    def install(self, cr, uid, ids, context=None):
        # Initialization of the configuration
        if context is None:
            context = {}
        """ install method """
        for vals in self.read(cr, uid, ids, context=context):
            self.pool['informal.reference'].unlink_rest(
                cr, uid, vals.get('informal_reference_ids', []))
            self.update_field(cr, uid, vals, context=context)
        return {'type': 'ir.actions.client', 'tag': 'reload', }


class FieldMergeWay(models.Model):
    _name = 'field.merge.way'

    name = new_api_fields.Char(required=True, translate=True)
    predefine = new_api_fields.Boolean()
    code = new_api_fields.Text(required=True, default='''
        #  Python code to return on result var the value of active field
        #  result = False
        #  self, dst_obj, src_objs, field are able to use:
        #  self => active strategy (on new api).
        #  dst_obj => merge destination object.
        #  src_objs => merge source objects without dst_obj.
        #  field => field to apply merge way.
        ''')

    _sql_constraints = [
        ('name_unique', 'unique (name)', 'Strategy must be unique!')]

    def apply(self, dst_obj, src_objs, field):
        method = (
            getattr(self, self.code, None) if self.predefine else self.custom)
        try:
            return method(dst_obj, src_objs, field) if method else None
        except:
            logger.exception(
                'An error happen trying to execute the Specific Merge '
                'Way python code for Model: %s, Field: %s,'
                'Destination id: %s and Source ids: %s' %
                (field.model, field.field_description, str(dst_obj.id),
                 str(src_objs.ids)))

    def add(self, dst_obj, src_objs, field):
        '''
        not applicable to: selection, many2one, date, datetime
        '''
        result = getattr(dst_obj, field.name, None)
        if field.ttype == 'char':
            union = ' '
        elif field.ttype == 'text':
            union = '\n ********************************************* \n'
        else:
            union = False
        for obj in src_objs:
            temp = getattr(obj, field.name, None)
            if result and temp:
                result += union + temp if union else temp
            elif not result:
                result = temp
        return result

    def average(self, dst_obj, src_objs, field):
        '''Applicable to: integer and float

        '''
        result = getattr(dst_obj, field.name, 0)
        count = 1 if result not in [False, None] else 0
        for obj in src_objs:
            temp = getattr(obj, field.name, None)
            if not any(var in [False, None] for var in (result, temp)):
                result += temp
                count += 1
        return result / count if result and count else 0

    def max(self, dst_obj, src_objs, field):
        '''
        not applicable to:
        '''
        return self._max_min(dst_obj, src_objs, field, gt)

    def min(self, dst_obj, src_objs, field):
        '''
        not applicable to:
        '''
        return self._max_min(dst_obj, src_objs, field, lt)

    def _max_min(self, dst_obj, src_objs, field, operator):
        result = getattr(dst_obj, field.name, None)
        for obj in src_objs:
            temp = getattr(obj, field.name, None)
            if not any(var in [None, False] for var in [result, temp]):
                result = temp if operator(temp, result) else result
            elif not result and temp:
                result = temp
        return result

    def custom(self, dst_obj, src_objs, field):
        local_dict = locals()
        local_dict.update(globals().get('__builtins__', {}))
        safe_eval(self.code, local_dict, mode='exec', nocopy=True)
        return local_dict['result']


class FieldMergeWayRel(models.Model):
    _name = 'field.merge.way.rel'

    name = new_api_fields.Many2one('ir.model.fields', required=True)
    merge_way = new_api_fields.Many2one('field.merge.way', required=True)
    model = new_api_fields.Many2one('ir.model', required=True)

    @api.multi
    def merge(self, dst_obj, src_objs):
        res = {}
        for item in self:
            val = item.merge_way.apply(dst_obj, src_objs, item.name)
            if val is not None:
                res[item.name.name] = val
        return res
