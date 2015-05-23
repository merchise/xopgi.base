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


class object_merger(orm.TransientModel):
    _name = 'object.merger'
    _description = 'Merge objects'

    _columns = {'name': fields.char('Name', size=16), }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        object_ids = context.get('active_ids', [])
        if object_ids:
            self._check_quantity(cr, uid, object_ids, context=context)
        res = super(object_merger, self).fields_view_get(cr, uid, view_id,
                                                         view_type,
                                                         context=context,
                                                         toolbar=toolbar,
                                                         submenu=submenu)
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
        obj = self.pool['ir.config_parameter']
        q = obj.get_param(cr, uid, 'objects_to_merge', 3, context=context)
        if ids and int(q) < len(ids):
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
        # init a new transaction to check for references on alias_defaults.
        cr.commit()
        self._check_on_alias_defaults(cr, uid, object_id, object_ids,
                                      active_model, context=context)
        return {'type': 'ir.actions.act_window_close'}

    def _merge(self, cr, active_model, object_id, object_ids, context=None):
        '''Do merge object_ids: first verify if at less 2 object_ids exist
        and one of they are object_id, then update all references of any
        object_ids to object_id and at the end deactivate or delete
        object_ids.

        '''
        model_pool = self.pool.get(active_model)
        object_ids = model_pool.exists(cr, SUPERUSER_ID, object_ids,
                                       context=context)
        if object_ids and object_id in object_ids and len(object_ids) > 1:
            object_ids.remove(object_id)
            self._check_fks(cr, active_model, object_id, object_ids)
            self._check_references(cr, active_model, object_id, object_ids)
            active_col = (model_pool._columns.get('active')
                          if hasattr(model_pool, '_columns') else False)
            if active_col and not isinstance(active_col, fields.function):
                return model_pool.write(cr, SUPERUSER_ID, object_ids,
                                        {'active': False}, context=context)
            return model_pool.unlink(cr, SUPERUSER_ID, object_ids,
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

    def _check_fks(self, cr, active_model, object_id, object_ids):
        '''Get all relational field with active_model and send to update it.
        :param cr:
        :param active_model:
        :param object_id:
        :param object_ids:
        :return:
        '''
        cr.execute("SELECT name, model, ttype "
                   "FROM ir_model_fields "
                   "WHERE relation=%s and ttype not in ('one2many');",
                   (active_model, ))
        for field_name, model_name, ttype in cr.fetchall():
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
                             value=object_id, ids=object_ids)

    def _upd_fk(self, cr, table, field, value, ids):
        '''Update foreign key (field) to destination value (value) where
        actual field value are in merging object ids (ids).
        if not constraint involve the field to update.
            Update all matching rows
        else
            check one by one if can update and update it or delete.

        '''
        constraints = self._get_contraints(cr, table, field)
        if not constraints:
            query = """UPDATE {model} SET {field}={object_id}
                           WHERE {field} IN ({filter});"""
            cr.execute(query.format(
                model=table,
                field=field,
                object_id=str(value),
                filter=','.join([str(i) for i in ids])
            ))
            return
        all_columns = []
        for columns in constraints:
            all_columns.extend(columns)
        all_columns = set(all_columns)
        value_parser = lambda val: (str(val) if isinstance(val, integer_types)
                                    else "'%s'" % str(val))

        def check_constraints(filters):
            '''
            Revisar si hay alguna fila que contenga los mismos valores que
            la que se está intentando actualizar de forma que se viole
            alguna restricción de tipo unique.

            :return: False if any violation detected else True

            '''
            filters.append('%s=%s' % (field, str(value)))
            for columns in constraints:
                const_filters = [arg for arg in filters
                                 if arg.split('=')[0] in columns]
                cr.execute('''SELECT {field} FROM {model}
                              WHERE {filters}'''.format(
                    field=field,
                    model=table,
                    filters=' AND '.join(const_filters)
                ))
                if cr.rowcount:
                    return False
            return True

        def upd_del(action_update, filters):
            '''
            Update or Delete rows matching with filters passed.
            :param action_update: if True Update query are executed else
            Delete query are executed
            :return:
            '''
            filters.append('%s=%s' % (field, row.get(field)))
            query_filters = ' AND '.join(filters)
            if action_update:
                query = """UPDATE {model} SET {field}={object_id}
                           WHERE {filters};"""
                cr.execute(query.format(model=table, field=field,
                                        object_id=str(value),
                                        filters=query_filters))
            else:
                query = """DELETE FROM {model}
                           WHERE {filters};"""
                cr.execute(query.format(model=table,
                                        filters=query_filters))
        query = '''SELECT {fields} FROM {model}
                   WHERE {field} IN ({filter})'''
        cr.execute(query.format(
            fields=', '.join(all_columns),
            model=table,
            field=field,
            filter=','.join([str(i) for i in ids])
        ))
        for row in cr.dictfetchall():
            filters = ['%s=%s' % (field_name, value_parser(field_value))
                       for field_name, field_value in row.items()
                       if field_name != field]
            upd_del(check_constraints(list(filters)), filters)

    def _check_references(self, cr, active_model, object_id, object_ids):
        '''Get all reference field and send to update it.
        '''
        cr.execute(
            "SELECT name, model "
            "FROM ir_model_fields "
            "WHERE ttype = 'reference' AND model!=%s;", (active_model,))
        _update = lambda t, f, mf=False: (
            self._upd_reference(cr, table=t, model=active_model,
                                field=f, value=object_id,
                                ids=object_ids, model_field=mf))
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
        REFERECES = [
            # (table_name, id_field, model_field)
            ('mail_followers', 'res_id', 'res_model'),
            ('ir_attachment', 'res_id', 'res_model'),
            ('mail_message', 'res_id', 'model'),
            ('ir_model_data', 'res_id', 'model'),
            ('wkf_triggers', 'res_id', 'model'),
            ('mail_compose_forward', 'res_id', 'model'),
            ('mail_compose_message', 'res_id', 'model')
        ]

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
        for table, field, model_field in REFERECES:
            if _check_field_exist(table, (field, model_field)):
                _update(table, field, model_field)

    def _upd_reference(self, cr, table, model, field, value, ids,
                       model_field=False):
        '''Update reference (field) to destination value (value) where
        actual field value are in merging object ids (ids).
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
                query = """UPDATE {table} SET {field}={object_id}
                               WHERE {field} IN ({filter})
                                  AND {model_field}='{model}';"""
                cr.execute(query.format(table=table, field=field,
                                        object_id=str(value),
                                        filter=','.join([str(i) for i in ids]),
                                        model_field=model_field,
                                        model=model))
                return
            for _id in ids:
                query = ("UPDATE {table} "
                         "SET {field}='{model},{dst_id}' " +
                         "WHERE " + SUBQUERY[0])
                cr.execute(query.format(table=table, field=field, model=model,
                                        dst_id=str(value), id=str(_id)))
            return
        all_columns = []
        for columns in constraints:
            all_columns.extend(columns)
        all_columns = set(all_columns)
        value_parser = lambda val: (str(val) if isinstance(val, integer_types)
                                    else "'%s'" % str(val))

        def check_constraints(filters):
            '''
            Revisar si hay alguna fila que contenga los mismos valores que
            la que se está intentando actualizar de forma que se viole
            alguna restricción de tipo unique.

            :return: False if any violation detected else True

            '''
            query_dict = dict(field=field, model=model, id=str(value))
            filters.append(SUBQUERY[0].format(**query_dict))
            filters.append('%s=%s' % (field, str(value)))
            for columns in constraints:
                const_filters = [arg for arg in filters if
                                 arg.split('=')[0] in columns]
                cr.execute(
                    "SELECT {field} FROM {table} WHERE {filters}".format(
                        field=field,
                        table=table,
                        filters=' AND '.join(const_filters)
                    )
                )
                if cr.rowcount:
                    return False
            return True

        def upd_del(action_update, filters, _id):
            '''
            Update or Delete rows matching with filters passed.
            :param action_update: if True Update query are executed else
            Delete query are executed
            :return:
            '''
            query_dict = dict(field=field, model=model, id=str(_id))
            filters.append(SUBQUERY[0].format(**query_dict))
            query_filters = ' AND '.join(filters)
            if action_update:
                query = ("UPDATE {table} SET " + SUBQUERY[0] +
                         " WHERE {filters};")
                cr.execute(query.format(table=table, field=field,
                                        model=model, id=str(value),
                                        filters=query_filters))
            else:
                query = """DELETE FROM {table}
                           WHERE {filters};"""
                cr.execute(query.format(table=table, filters=query_filters))
        query = ("SELECT {fields} FROM {table} WHERE " + ' AND '.join(SUBQUERY))
        for _id in ids:
            cr.execute(
                query.format(fields=', '.join(all_columns), table=table,
                             field=field, model=model, id=_id,
                             model_field=model_field))
            for row in cr.dictfetchall():
                filters = ['%s=%s' % (field_name, value_parser(field_value))
                           for field_name, field_value in row.items()
                           if field_name != field]
                upd_del(check_constraints(list(filters)), filters, _id)

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
