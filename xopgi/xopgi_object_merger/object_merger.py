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

from six import integer_types

from .res_config import IS_MODEL_ID


class object_merger(orm.TransientModel):
    _name = 'object.merger'
    _description = 'Merge objects'

    _columns = {'name': fields.char('Name', size=16), }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        object_ids = context.get('active_ids', [])
        active_model = context.get('active_model')
        if object_ids:
            self._check_quantity(cr, uid, object_ids, active_model,
                                 context=context)
        res = super(object_merger, self).fields_view_get(cr, uid, view_id,
                                                         view_type,
                                                         context=context,
                                                         toolbar=toolbar,
                                                         submenu=submenu)
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

    def _browse_active_model(self, cr, active_model):
        model_obj = self.pool['ir.model']
        model = model_obj.browse(
            cr,
            SUPERUSER_ID,
            model_obj.search(cr, SUPERUSER_ID, [('model', '=', active_model)])
        )
        return model and model[0] or False

    def _check_quantity(self, cr, uid, ids, active_model, context=None):
        '''Check for groups_id of uid and if it are not merger manager check
        limit quantity of objects to merge.

        '''
        if len(ids) < 2:
            raise osv.except_osv(
                _('Information!'),
                _('At less two items are necessary for merge.')
            )
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
        model = self._browse_active_model(cr, active_model)
        if model and 0 < model.merge_limit < len(ids):
            raise osv.except_osv(_('Warning!'),
                                 _('You can`t merge so much objects '
                                   'at one time.'))
        return True

    def action_merge(self, cr, uid, ids, context=None):
        """
        Merges two or more objects
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
        src_ids = context.get('active_ids', [])
        field_to_read = context.get('field_to_read')
        field_list = field_to_read and [field_to_read] or []
        object = self.read(cr, uid, ids[0], field_list, context=context)
        if object and field_list and object[field_to_read]:
            dst_id = object[field_to_read][0]
        else:
            raise orm.except_orm(_('Configuration Error!'),
                                 _('Please select one value to keep'))
        self._merge(cr, active_model, dst_id, src_ids, context=context)
        # init a new transaction to check for references on alias_defaults.
        cr.commit()
        self._check_on_alias_defaults(cr, dst_id, src_ids,
                                      active_model, context=context)
        return {'type': 'ir.actions.act_window_close'}

    def _merge(self, cr, active_model, dst_id, src_ids, context=None):
        '''Do merge src_ids: first verify if at less 2 src_ids exist
        and one of they are dst_id, then update all references of any
        src_ids to dst_id and at the end deactivate or delete
        src_ids.

        '''
        model_pool = self.pool.get(active_model)
        src_ids = model_pool.exists(cr, SUPERUSER_ID, src_ids,
                                       context=context)
        if src_ids and dst_id in src_ids and len(src_ids) > 1:
            src_ids.remove(dst_id)
            self._check_fks(cr, active_model, dst_id, src_ids)
            self._check_references(cr, active_model, dst_id, src_ids)
            active_col = (model_pool._columns.get('active')
                          if hasattr(model_pool, '_columns') else False)
            if active_col and not isinstance(active_col, fields.function):
                return model_pool.write(cr, SUPERUSER_ID, src_ids,
                                        {'active': False}, context=context)
            return model_pool.unlink(cr, SUPERUSER_ID, src_ids,
                                     context=context)

    def _get_contraints(self, cr, table, field):
        '''
        Get a list of unique constraints that involve column to update
        (foreign key from merging model)
        :param cr:
        :param table: db table to update
        :param field: column to update
        :return: list of (list of fields involve on each constraint) or
        empty list if not unique constraint involve column tu update
        '''
        cr.execute("""
            SELECT
              kcu.column_name,
              tc.constraint_name
            FROM
              information_schema.key_column_usage kcu,
              information_schema.key_column_usage kcuw,
              information_schema.table_constraints tc
            WHERE
              kcu.constraint_catalog = tc.constraint_catalog AND
              kcu.constraint_schema = tc.constraint_schema AND
              kcu.constraint_name = tc.constraint_name AND
              kcuw.constraint_catalog = tc.constraint_catalog AND
              kcuw.constraint_schema = tc.constraint_schema AND
              kcuw.constraint_name = tc.constraint_name AND
              tc.constraint_type = 'UNIQUE' AND
              tc.table_name = %s AND
              kcuw.column_name = %s
              """, (table, field))
        constraints = {}
        for column_name, constraint_name in cr.fetchall():
            if constraint_name not in constraints:
                constraints[constraint_name] = []
            constraints[constraint_name].append(column_name)
        return constraints.values()

    def _check_constraints(self, cr, table, field, dst_id, filters,
                          constraints, model='', subquery='{field}={id}'):
        '''
        Revisar si hay alguna fila que contenga los mismos valores que
        la que se está intentando actualizar de forma que se viole
        alguna restricción de tipo unique.

        :return: False if any violation detected else True

        '''
        filters.append(subquery.format(field=field, model=model, id=str(dst_id)))
        for columns in constraints:
            const_filters = [arg for arg in filters if
                             arg.split('=')[0] in columns]
            cr.execute("SELECT {field} FROM {table} WHERE {filters}".format(
                field=field, table=table,
                filters=' AND '.join(const_filters)))
            if cr.rowcount:
                return False
        return True

    def _upd_del(self, action_update, cr, table, field, dst_id, filters,
                src_id, model='', subquery='{field}={id}'):
        '''
        Update or Delete rows matching with filters passed.
        :param action_update: if True Update query are executed else
        Delete query are executed
        :return:
        '''
        filters.append(subquery.format(field=field, model=model, id=str(src_id)))
        query_filters = ' AND '.join(filters)
        if action_update:
            query = "UPDATE {table} SET " + subquery + " WHERE {filters};"
            cr.execute(query.format(table=table, field=field, model=model,
                                    id=str(dst_id), filters=query_filters))
        else:
            query = """DELETE FROM {table} WHERE {filters};"""
            cr.execute(query.format(table=table, filters=query_filters))

    def _check_fks(self, cr, active_model, dst_id, src_ids):
        '''Get all relational field with active_model and send to update it.
        :param cr:
        :param active_model:
        :param dst_id:
        :param src_ids:
        :return:
        '''
        query = """
          SELECT name, model, ttype
          FROM ir_model_fields
          WHERE relation=%s AND ttype != 'one2many'"""
        query_args = [active_model]
        model = self._browse_active_model(cr, active_model)
        if model and not model.merge_cyclic:
            query += " AND model!=%s"
            query_args.append(active_model)
        cr.execute(query, tuple(query_args))
        fks = cr.fetchall()
        for field_name, model_name, ttype in fks:
            pool = self.pool.get(model_name)
            if not pool:
                continue
            if ((not pool) or (hasattr(pool, '_auto') and not pool._auto) or
                    hasattr(pool, '_check_time')):
                continue
            if hasattr(pool, '_columns'):
                column = pool._columns.get(field_name, False)
                if (not column) or (isinstance(column, fields.function) and
                                    not column.store):
                    continue
                if ttype == 'many2one':
                    if hasattr(pool, '_table'):
                        model = pool._table
                    else:
                        model = model_name.replace('.', '_')
                elif ttype == 'many2many':
                    model, _, field_name = column._sql_names(pool)
                else:
                    continue
                self._upd_fk(cr, table=model, field=field_name,
                             dst_id=dst_id, src_ids=src_ids)

    def _upd_fk(self, cr, table, field, dst_id, src_ids):
        '''Update foreign key (field) to destination value (dst_id) where
        actual field value are in merging object ids (src_ids).
        if not constraint involve the field to update.
            Update all matching rows
        else
            check one by one if can update and update it or delete.

        '''
        constraints = self._get_contraints(cr, table, field)
        if not constraints:
            query = """UPDATE {model} SET {field}={dst_id}
                           WHERE {field} IN ({filter});"""
            cr.execute(query.format(
                model=table,
                field=field,
                dst_id=str(dst_id),
                filter=','.join([str(i) for i in src_ids])
            ))
            return
        all_columns = []
        for columns in constraints:
            all_columns.extend(columns)
        all_columns = set(all_columns)
        value_parser = lambda val: (str(val) if isinstance(val, integer_types)
                                    else "'%s'" % str(val))
        query = '''SELECT {fields} FROM {model}
                   WHERE {field} IN ({filter})'''
        cr.execute(query.format(
            fields=', '.join(all_columns),
            model=table,
            field=field,
            filter=','.join([str(i) for i in src_ids])
        ))
        ck_ctr = lambda f: self._check_constraints(cr, table, field,
                                                   dst_id, f, constraints)
        upd_del = lambda a, f, src_id: self._upd_del(a, cr, table, field,
                                                     dst_id, f, src_id)
        for row in cr.dictfetchall():
            filters = ['%s=%s' % (field_name, value_parser(field_value))
                       for field_name, field_value in row.items()
                       if field_name != field]
            upd_del(ck_ctr(filters), filters, row.get(field))

    def _check_references(self, cr, active_model, dst_id, src_ids):
        '''Get all reference field and send to update it.
        '''
        cr.execute(
            "SELECT name, model "
            "FROM ir_model_fields "
            "WHERE ttype = 'reference' AND model!=%s;", (active_model,))
        _update = lambda t, f, mf=False, m=active_model: (
            self._upd_reference(cr, table=t, model=m,
                                field=f, dst_id=dst_id,
                                src_ids=src_ids, model_field=mf))
        for field_name, model_name in cr.fetchall():
            pool = self.pool.get(model_name)
            if not pool:
                continue
            if ((not pool) or (hasattr(pool, '_auto') and not pool._auto)
                    or hasattr(pool, '_check_time')):
                continue
            if hasattr(pool, '_columns'):
                column = pool._columns.get(field_name, False)
                if (not column) or (isinstance(column, fields.function)
                                    and not column.store):
                    continue
            if hasattr(pool, '_table'):
                table = pool._table
            else:
                table = model_name.replace('.', '_')
            _update(table, field_name)

        def _check_field_exist(table_name, column_names):
            query = """
              SELECT column_name
              FROM information_schema.columns
              WHERE table_schema='public' AND table_name=%s AND column_name=%s
            """
            for column_name in column_names:
                cr.execute(query, (table_name, column_name))
                if not cr.rowcount:
                    return False
            return True
        for ref in self.pool['informal.reference'].get_all(cr, SUPERUSER_ID):
            if _check_field_exist(ref.table_name, (ref.id_field_name,
                                                   ref.model_field_name)):
                if ref.model_field_value == IS_MODEL_ID:
                    args = [('model', '=', active_model)]
                    model_id = self.pool['ir.model'].search(cr,
                                                            SUPERUSER_ID,
                                                            args)
                    if model_id and model_id[0]:
                        _update(ref.table_name, ref.id_field_name,
                                ref.model_field_name, str(model_id[0]))
                else:
                    _update(ref.table_name, ref.id_field_name,
                            ref.model_field_name)

    def _upd_reference(self, cr, table, model, field, dst_id, src_ids,
                       model_field=False):
        '''Update reference (field) to destination value (dst_id) where
        actual field value are in merging object ids (src_ids).
        if not constraint involve the field to update.
            Update all matching rows
        else
            check one by one if can update and update it or delete.

        '''
        constraints = self._get_contraints(cr, table, field)
        SUBQUERY = (["{field} = {id}", "{model_field}='{model}'"]
                    if model_field else ["{field} = '{model},{id}'"])
        if not constraints:
            if model_field:
                query = """UPDATE {table} SET {field}={dst_id}
                               WHERE {field} IN ({filter})
                                  AND {model_field}='{model}';"""
                cr.execute(query.format(table=table, field=field,
                                        dst_id=str(dst_id),
                                        filter=','.join([str(i) for i in src_ids]),
                                        model_field=model_field,
                                        model=model))
                return
            for _id in src_ids:
                query = ("UPDATE {table} "
                         "SET {field}='{model},{dst_id}' " +
                         "WHERE " + SUBQUERY[0])
                cr.execute(query.format(table=table, field=field, model=model,
                                        dst_id=str(dst_id), id=str(_id)))
            return
        all_columns = []
        for columns in constraints:
            all_columns.extend(columns)
        all_columns = set(all_columns)
        value_parser = lambda val: (str(val) if isinstance(val, integer_types)
                                    else "'%s'" % str(val))
        query = ("SELECT {fields} FROM {table} WHERE " + ' AND '.join(SUBQUERY))
        ck_ctr = lambda f: self._check_constraints(
            cr, table, field, dst_id, f, constraints, model, SUBQUERY[0])
        upd_del = lambda a, f, src_id: self._upd_del(a, cr, table, field,
                                                     dst_id, f, src_id,
                                                     model, SUBQUERY[0])
        for src_id in src_ids:
            cr.execute(
                query.format(fields=', '.join(all_columns), table=table,
                             field=field, model=model, id=src_id,
                             model_field=model_field))
            for row in cr.dictfetchall():
                filters = ['%s=%s' % (field_name, value_parser(field_value))
                           for field_name, field_value in row.items()
                           if field_name != field]
                upd_del(ck_ctr(filters), filters, src_id)

    def _check_on_alias_defaults(self, cr, dst_id,
                                 src_ids, model, context=None):
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
                   "WHERE relation='%s';" % model)
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
                    if val in src_ids and val != dst_id:
                        defaults_dict[field] = dst_id
                        _update_alias(alias_id, defaults_dict)
                else:
                    res_val = []
                    for rel_item in val:
                        rel_ids = rel_item[-1]
                        if isinstance(rel_ids, (tuple, list)):
                            wo_partner_ids = [i for i in rel_ids if i not in src_ids]
                            if wo_partner_ids != rel_ids:
                                rel_ids = set(wo_partner_ids + [dst_id])
                        elif rel_ids in src_ids and val != dst_id:
                            rel_ids = dst_id
                        res_val.append(tuple(rel_item[:-1]) + (rel_ids,))
                    if val != res_val:
                        defaults_dict[field] = res_val
                        _update_alias(alias_id, defaults_dict)
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
