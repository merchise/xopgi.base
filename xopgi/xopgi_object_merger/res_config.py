#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_object_merger.res_config
# --------------------------------------------------------------------------
# Copyright (c) 2014, 2015 Merchise Autrement and Contributors
# All rights reserved.
#
# Author: Merchise Autrement
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.


from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
import copy


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
    }

    _defaults = {'object_merger_model': False, 'merge_cyclic': False,
                 'merge_limit': 0}

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


class object_merger_settings(osv.osv_memory):
    _name = 'object.merger.settings'
    _inherit = 'res.config.settings'

    def _get_objects_to_merge(self, cr, uid, ids, name, arg, context=None):
        obj = self.pool['ir.config_parameter']
        q = int(obj.get_param(cr, uid, 'objects_to_merge', 0, context=context))
        return {i: q for i in ids}

    def _set_objects_to_merge(self, cr, uid, _id, field_name, field_value,
                            arg, context=None):
        if field_value and field_value < 0:
            raise osv.except_osv(
                'Error!',
                _('The limit must be a positive number.'))
        obj = self.pool['ir.config_parameter']
        return obj.set_param(cr, uid, 'objects_to_merge',
                             value=field_value or '0',
                             context=context)

    _columns = {
        'models_ids':
            fields.many2many(
                'ir.model', 'object_merger_settings_model_rel',
                'object_merger_id', 'model_id', 'Models',
                domain=[('osv_memory', '=', False)],
                context={'object_merger_settings': True}
            ),
        'limit':
            fields.function(
                _get_objects_to_merge, fnct_inv=_set_objects_to_merge,
                method=True, string='Object to merge limit', type='integer',
                help='Limit quantity of objects to allow merge at one time.'
            ),
    }

    def _get_default_object_merger_models(self, cr, uid, context=None):
        return self.pool.get('ir.model').search(cr, uid, [
            ('object_merger_model', '=', True)], context=context)

    _defaults = {
        'limit': lambda self, cr, uid, c: (
            self._get_objects_to_merge(cr, uid, [0], None, None, context=c)[0]
        ),
        'models_ids': _get_default_object_merger_models,
    }

    def update_field(self, cr, uid, vals, context=None):
        ## Init ##
        if context is None:
            context = {}
        model_ids = []
        model_obj = self.pool.get('ir.model')
        action_obj = self.pool.get('ir.actions.act_window')
        value_obj = self.pool.get('ir.values')
        field_obj = self.pool.get('ir.model.fields')
        ## Process ##
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
            un_val_ids = value_obj.search(cr, uid, [
                ('value', '=', "ir.actions.act_window," + str(unlink_id)), ],
                                          context=context)
            value_obj.unlink(cr, uid, un_val_ids, context=context)
        # Put all models which were selected before back to not an object_merger
        model_not_merge_ids = model_obj.search(
            cr,
            uid,
            [('id', 'not in', model_ids), ('object_merger_model', '=',True)],
            context=context
        )
        model_obj.write(cr, uid, model_not_merge_ids,
                        {'object_merger_model': False}, context=context)
        # Put all models which are selected to be an object_merger
        model_obj.write(cr, uid, model_ids, {'object_merger_model': True},
                        context=context)
        ### Create New Fields ###
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
                'context': "{'field_to_read':'%s'}" % field_name,
                'view_mode': 'form', 'target': 'new', }, context=context)
            value_obj.create(
                cr,
                uid,
                {'name': "%s " % model['name'] + _("Merger"),
                 'model': model['model'], 'key2': 'client_action_multi',
                 'value': "ir.actions.act_window," + str(act_id),},
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

    def create(self, cr, uid, vals, context=None):
        """ create method """
        vals2 = copy.deepcopy(vals)
        result = super(object_merger_settings, self).create(cr, uid, vals2,
                                                            context=context)
        ## Fields Process ##
        self.update_field(cr, uid, vals, context=context)
        return result

    def install(self, cr, uid, ids, context=None):
        # Initialization of the configuration
        if context is None:
            context = {}
        """ install method """
        for vals in self.read(cr, uid, ids, context=context):
            result = self.update_field(cr, uid, vals, context=context)
        return {'type': 'ir.actions.client', 'tag': 'reload', }

    # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
