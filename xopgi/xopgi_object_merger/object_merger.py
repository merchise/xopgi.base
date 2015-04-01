#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_object_merge.object_merger
# --------------------------------------------------------------------------
# Copyright (c) 2014 Merchise Autrement and Contributors
# All rights reserved.
#
# Author: Merchise Autrement
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.

from openerp import SUPERUSER_ID

from openerp.osv import orm, osv, fields

from openerp.tools.translate import _
from openerp.tools import ustr


class object_merger(orm.TransientModel):
    _name = 'object.merger'
    _description = 'Merge objects'

    _columns = {'name': fields.char('Name', size=16), }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        object_ids = context.get('active_ids',[])
        self._check_quantity(cr, uid, object_ids, context=context)
        res = super(object_merger, self).fields_view_get(cr, uid, view_id,
                                                         view_type,
                                                         context=context,
                                                         toolbar=toolbar,
                                                         submenu=submenu)
        object_ids = context.get('active_ids', [])
        active_model = context.get('active_model')
        field_name = 'x_' + (
            active_model and active_model.replace('.', '_') or '') + '_id'
        if object_ids:
            view_part = """
            <label for='""" + field_name + """'/>
              <div>
                <field name='""" + field_name + """' required="1"
                       domain="[(\'id\', \'in\', """ + str(object_ids) + """)]"/>
              </div>
            """
            res['arch'] = res['arch'].decode('utf8').replace(
                """<separator string="to_replace"/>""", view_part
            )
            field = self.fields_get(cr, uid, [field_name], context=context)
            res['fields'] = field
            res['fields'][field_name]['domain'] = [('id', 'in', object_ids)]
            res['fields'][field_name]['required'] = True
        return res

    def _check_quantity(self, cr, uid, ids, context=None):
        '''Check for groups_id of uid and if it are not merger manager check
        limit quantity of objects to merge.

        '''
        if uid == SUPERUSER_ID:
            return True
        pool = self.pool.get('ir.model.data')
        dummy, group_id = pool.get_object_reference(cr, uid,
                                                    'xopgi_object_merger',
                                                    'group_merger_manager')
        if group_id:
            user_data = self.pool['res.users'].read(cr, uid, uid,
                                                    ['groups_id'],
                                                    context=context)
            if user_data and group_id in user_data['groups_id']:
                return True
        obj = self.pool['ir.config_parameter']
        q = obj.get_param(cr, uid, 'objects_to_merge', 3, context=context)
        if ids and int(q) < len(ids):
            raise osv.except_osv(_('Warning!'),
                                 _('You can`t merge so much objects '
                                   'at one time.'))
        return True

    def action_merge(self, cr, uid, ids, context=None):

        """
        Merges two (or more objects
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of Lead to Opportunity IDs
        @param context: A standard dictionary for contextual values

        @return : {}
        """
        if context is None:
            context = {}
        active_model = context.get('active_model')
        if not active_model:
            raise orm.except_orm(_('Configuration Error!'),
                                 _('The is no active model defined!'))
        object_ids = context.get('active_ids', [])
        field_to_read = context.get('field_to_read')
        field_list = field_to_read and [field_to_read] or []
        object = self.read(cr, uid, ids[0], field_list, context=context)
        if object and field_list and object[field_to_read]:
            object_id = object[field_to_read][0]
        else:
            raise orm.except_orm(_('Configuration Error!'),
                                 _('Please select one value to keep'))
        self._merge(cr, active_model, object_id, object_ids, context=context)
        self._check_on_alias_defaults(cr, uid, object_id, object_ids,
                                      active_model, context=context)
                # TODO: refactorizar el módulo original para liminar el
                # error de violación de restricciones en la BD.
        return {'type': 'ir.actions.act_window_close'}

    def _merge(self, cr, active_model, object_id, object_ids, context=None):
        cr.execute(
            "SELECT name, model FROM ir_model_fields WHERE relation=%s and ttype not in ('many2many', 'one2many');",

            (active_model, ))
        for name, model_raw in cr.fetchall():
            if hasattr(self.pool.get(model_raw), '_auto'):
                if not self.pool.get(model_raw)._auto:
                    continue
            if hasattr(self.pool.get(model_raw), '_check_time'):
                continue
            else:
                if hasattr(self.pool.get(model_raw), '_columns'):
                    if self.pool.get(model_raw)._columns.get(name,
                                                             False) and (
                                isinstance(self.pool.get(model_raw
                                )._columns[name],
                                           fields.many2one) or isinstance(
                                    self.pool.get(model_raw)._columns[name],
                                    fields.function) and self.pool.get(model_raw)._columns[name].store):
                        if hasattr(self.pool.get(model_raw), '_table'):
                            model = self.pool.get(model_raw)._table
                        else:
                            model = model_raw.replace('.', '_')
                        requete = "UPDATE " + model + " SET " + name + "=" + str(
                            object_id) + " WHERE " + ustr(name) + " IN " + str(tuple(object_ids)) + ";"
                        cr.execute(requete)
        cr.execute(
            "select name, model from ir_model_fields where relation=%s and ttype in ('many2many');",
            (active_model, ))
        for field, model in cr.fetchall():
            field_data = self.pool.get(model) and self.pool.get(model)._columns.get(field, False) and (
                isinstance(self.pool.get(model)._columns[field],
                           fields.many2many) or isinstance(
                    self.pool.get(model)._columns[field], fields.function) and
                self.pool.get(model)._columns[field].store) and self.pool.get(model)._columns[field] or False
            if field_data:
                model_m2m, rel1, rel2 = field_data._sql_names(self.pool.get(model))
                requete = "UPDATE " + model_m2m + " SET " + rel2 + "=" + str(
                    object_id) + " WHERE " + ustr(rel2) + " IN " + str(tuple(object_ids)) + ";"
                cr.execute(requete)
        unactive_object_ids = model_pool.search(cr, SUPERUSER_ID,
                                                [('id', 'in', object_ids),
                                                 ('id', '<>', object_id)],
                                                context=context)
        model_pool.write(cr, SUPERUSER_ID, unactive_object_ids, {'active': False},
                         context=context)

    def _check_on_alias_defaults(self, cr, uid, dst_id,
                                 ids, model, context=None):
        """Check if any of merged partner_ids are referenced on any mail.alias
        and on this case update the references to the dst_partner_id.
        """
        alias_upd = self.pool['mail.alias'].write
        _update_alias = lambda _id, alias_defaults: alias_upd(
            cr,
            SUPERUSER_ID,
            _id,
            {'alias_defaults': str(alias_defaults)},
            context=context
        )
        query = """SELECT id, alias_defaults FROM mail_alias
                         WHERE alias_model_id = {model}
                         AND (alias_defaults LIKE '%''{field}''%')"""
        cr.execute("SELECT name, model_id, ttype FROM ir_model_fields "
                   "WHERE relation='%s';" (model,))
        read = cr.fetchall()
        for field, model_id, ttype in read:
            cr.execute(query.format(model=model_id, field=field))
            for alias_id, defaults in cr.fetchall():
                try:
                    defaults_dict = dict(eval(defaults))
                except Exception:
                    defaults_dict = {}
                val = defaults_dict.get(field, False)
                if not val:
                    continue
                if ttype == 'many2one':
                    if val in ids and val != dst_id:
                        defaults_dict[field] = dst_id
                        _update_alias(alias_id, defaults_dict)
                else:
                    res_val = []
                    for rel_item in val:
                        rel_ids = rel_item[-1]
                        if isinstance(rel_ids, (tuple, list)):
                            wo_partner_ids = [i for i in rel_ids if i not in ids]
                            if wo_partner_ids != rel_ids:
                                rel_ids = set(wo_partner_ids + [dst_id])
                        elif rel_ids in ids and val != dst_id:
                            rel_ids = dst_id
                        res_val.append(tuple(rel_item[:-1]) + (rel_ids,))
                    if val != res_val:
                        defaults_dict[field] = res_val
                        _update_alias(alias_id, defaults_dict)
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
