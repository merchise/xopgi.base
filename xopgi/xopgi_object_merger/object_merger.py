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

from xoeuf import api, fields, models, MAJOR_ODOO_VERSION
from xoeuf.odoo import _
from xoeuf.odoo.exceptions import Warning as UserError, AccessError

from xoeuf.models.proxy import IrModel

from six import string_types
from xoeuf.ui import CLOSE_WINDOW

from .res_config import IS_MODEL_ID


def get_filters(data, except_field):
    def tuple_parser(name, value):
        if value is None:
            res_val = 'Null'
            res_op = 'is'
        else:
            res_val = ("'%s'" % value
                       if isinstance(value, string_types)
                       else str(value))
            res_op = 'is' if isinstance(value, bool) else '='
        return name, res_op, res_val
    return [tuple_parser(field_name, field_value) for
            field_name, field_value in data.items()
            if field_name != except_field]


class object_merger(models.TransientModel):
    _name = 'object.merger'
    _description = 'Merge objects'

    name = fields.Char('Name', size=16)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(object_merger, self).fields_view_get(
            view_id,
            view_type,
            toolbar=toolbar,
            submenu=submenu
        )
        if view_type == 'form':
            object_ids = self._context.get('active_ids', [])
            active_model = self._context['active_model']
            if object_ids:
                self._check_quantity(active_model)
                field_name = 'x_%s_id' % active_model.replace('.', '_')
                view_part = """
                <field name="{field_name}"/>
                <separator string="{string}" colspan="4"/>
                <field name="info" nolabel="1" colspan="4"/>
                """.format(field_name=field_name, string=_("To merge"))
                res['arch'] = res['arch'].decode('utf8').replace(
                    """<separator string="to_replace"/>""", view_part
                )
                field = self.fields_get([field_name, 'info'])
                field_data = field[field_name]
                field_data.update(
                    domain=[('id', '=', object_ids)],
                    selection=self.env[active_model].sudo().name_get(),
                    required=True
                )
                res['fields'].update(field)
        return res

    if MAJOR_ODOO_VERSION < 10:
        @api.model
        def fields_get(self, fields_list=None, write_access=True, attributes=None):
            res = super(object_merger, self).fields_get(
                allfields=fields_list,
                write_access=write_access,
                attributes=attributes
            )
            if fields_list and 'info' in fields_list:
                active_model = self._context.get('active_model')
                fvg = lambda view: self.env[active_model].fields_view_get(
                    view_type=view
                )
                res.update(info=dict(
                    type='many2many',
                    relation=active_model,
                    views={k: fvg(k) for k in ['tree', 'form']}
                ))
            return res
    else:
        @api.model
        def fields_get(self, fields_list=None, attributes=None):
            res = super(object_merger, self).fields_get(
                allfields=fields_list,
                attributes=attributes
            )
            if fields_list and 'info' in fields_list:
                active_model = self._context.get('active_model')
                fvg = lambda view: self.env[active_model].fields_view_get(
                    view_type=view
                )
                res.update(info=dict(
                    type='many2many',
                    relation=active_model,
                    views={k: fvg(k) for k in ['tree', 'form']}
                ))
            return res

    @api.model
    def default_get(self, fields_list):
        res = super(object_merger, self).default_get(fields_list)
        if fields_list and 'info' in fields_list:
            res.update(info=self._context.get('active_ids', False))
        return res

    def _check_quantity(self, active_model):
        '''Check for groups_id of uid and if it are not merger manager check limit
        quantity of objects to merge.

        '''
        if len(self._context.get('active_ids', [])) < 2:
            raise UserError(
                _('Information!'),
                _('At less two items are necessary for merge.')
            )
        model = IrModel.sudo().search([('model', '=', active_model)], limit=1)
        if model and 0 < model.merge_limit < len(self._context.get('active_ids', [])):
            raise UserError(_('Warning!'),
                            _('You can`t merge so much objects at one time.'))
        return True

    @api.requires_singleton
    def action_merge(self):
        active_model = self._context.get('active_model')
        if not active_model:
            raise UserError(_('Configuration Error!'),
                            _('The is no active model defined!'))
        Model = self.env[active_model]
        sources = Model.browse(self._context.get('active_ids', []))
        attr = self._context.get('field_to_read')
        val = getattr(self, attr, None) if attr else None
        if not val:
            raise UserError(_('Configuration Error!'),
                            _('Please select one value to keep'))
        target = val[0]
        self.merge(sources, target)
        try:
            Model.read([])
            return target.get_formview_action()
        except AccessError:
            return CLOSE_WINDOW

    @api.model
    def merge(self, sources, target=None, deactivate=True):
        '''Merge all recordsets from `source` into `target`.

        If `target` is None, it defaults to the last-created record from
        `source`.

        If `deactivate` is True (the default), and the `sources` have an
        'active' field, we deactivate the sources instead of deleting them.

        Return False if no merge happened.  Otherwise, return True.

        .. rubric:: Merging trees.

        .. rubric:: Merging arbitrary graphs.

        '''
        sources = sources.sudo().exists()
        active_model = sources._name
        merge_way = IrModel.search([('model', '=', active_model)])
        if not target:
            target = sources.sorted(key=lambda date: date.create_date)[-1]
        sources -= target
        if sources:
            merge_way._merge(sources, target)
            self._check_fks(sources, target)
            self._check_references(sources, target)
            has_active = sources._fields.get('active', False)
            if has_active and deactivate:
                sources.write({'active': False})
            else:
                sources.unlink()
            return True
        else:
            return False

    def _get_contraints(self, table, field):
        '''Get unique constraints that involve `column` in `table`.

        :return: list of list of columns per constraint where `field` is
                 involved.

        '''
        self._cr.execute(
            """
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
              """,
            (table, field)
        )
        constraints = {}
        for column_name, constraint_name in self._cr.fetchall():
            data = constraints.setdefault(constraint_name, [])
            data.append(column_name)
        return constraints.values()

    def _check_constraints(self, table, field, target, filters,
                           model='', subquery='{field} = {id}'):
        '''Check unique constraints.

        :return: False if any violation detected else True

        '''
        constraints = self._get_contraints(table, field)
        for columns in constraints:
            if columns:
                query_filters = ' AND '.join(
                    ['%s %s %s' % f for f in filters] +
                    [subquery.format(field=field, model=model, id=target.id)])
            self._cr.execute("SELECT {field} FROM {table} WHERE {filters}".format(
                field=field, table=table, filters=query_filters))
            if self._cr.rowcount:
                return False
        return True

    def _upd_del(self, table, field, target, filters,
                 sources, model=None, subquery='{field}={id}'):
        '''
        Update or Delete rows matching with filters passed.
        :param action_update: if True Update query are executed else
        Delete query are executed
        :return:
        '''
        ok = self._check_constraints(table, field, target, filters,
                                     model=model, subquery=subquery)
        query_filters = ' AND '.join(
            ['%s %s %s' % f for f in filters] +
            [subquery.format(field=field, id=sources)])
        if ok:
            query = "UPDATE {table} SET " + subquery + " WHERE {filters};"
            self._cr.execute(query.format(table=table, field=field, model=model,
                             id=str(target.id), filters=query_filters))
        else:
            query = """DELETE FROM {table} WHERE {filters};"""
            self._cr.execute(query.format(table=table, filters=query_filters))

    @api.model
    def _check_fks(self, sources, target):
        '''Get all relational field with active_model and send to update it.
        '''
        query = """
          SELECT name, model, ttype
          FROM ir_model_fields
          WHERE relation=%(model)s AND ttype != 'one2many'"""
        args = dict(model=sources._name)
        model = IrModel.search([('model', '=', sources._name)])
        record = sources + target
        if model:
            self._cr.execute(query, args)
            fks = self._cr.fetchall()
        else:
            fks = []
        for field_name, model_name, ttype in fks:
            # When a model disappears, Odoo won't remove it from
            # ir_models_fields until the addon is removed.  So we can get a
            # model_name that it's not in the registry.  Ignore it.
            model_registry = self.env.registry.get(model_name)
            if not model_registry:
                continue
            if not getattr(model_registry, '_auto', False):
                # The model is not created by the ORM
                continue
            field = model_registry._fields.get(field_name, False)
            assert not field or field.relational
            if not field or not field.store:
                # Fields which are not in the
                continue
            if ttype == 'many2one':
                if hasattr(model_registry, '_table'):
                    table = model_registry._table
                else:
                    table = model_name.replace('.', '_')
            elif ttype == 'many2many':
                if MAJOR_ODOO_VERSION < 10:
                    modelname = self.env[model_name]
                    table, _x, field_name = field.column._sql_names(modelname)
                else:
                    table, field_name = field.relation, field.column2
            else:
                assert False
            self._upd_fk(
                table=table,
                field=field_name,
                sources=sources,
                target=target
            )
            field_names = []
            field_names.append(str(field_name))
            record._validate_fields(field_names)

    def _upd_fk(self, table, field, sources, target):
        '''Update foreign key (field) to destination value `target` where
        actual field value are in merging object `sources`.
        if not constraint involve the field to update.
            Update all matching rows
        else
            check one by one if can update and update it or delete.

        '''
        constraints = self._get_contraints(table, field)
        if not constraints:
            query = 'UPDATE {table} SET {field}={target} WHERE {field} IN ({filter});'
            self._cr.execute(query.format(
                table=table,
                field=field,
                target=target.id,
                filter=','.join(str(i) for i in sources.ids)
            ))
        else:
            query = 'SELECT {fields} FROM {model} WHERE {field} IN ({filter})'
            self._cr.execute(query.format(
                fields=', '.join(str(i) for i in constraints[0]),
                model=table,
                field=field,
                filter=','.join(str(i) for i in sources.ids)
            ))
            for row in self._cr.dictfetchall():
                filters = get_filters(row, field)
                self._upd_del(table, field, target, filters, row.get(field))

    def _check_references(self, sources, target):
        '''Get all reference field and send to update it.
        '''
        query = """
          SELECT name, model
          FROM ir_model_fields
          WHERE ttype = 'reference' AND model!=%(model)s;"""
        query_args = dict(model=sources._name)
        self._cr.execute(query, query_args)
        refks = self._cr.fetchall()
        for field_name, model_name in refks:
            model = self.env.registry(model_name)
            if not model:
                continue
            if not getattr(model, '_auto', False):
                continue
            if hasattr(model, '_fields'):
                field = model._fields.get(field_name, False)
                if not field or not field.store:
                    continue
            if hasattr(model, '_table'):
                table = model._table
            else:
                table = model_name.replace('.', '_')
            self._upd_reference(
                table=table,
                field=field_name,
                sources=sources,
                target=target,
                model=model_name
            )
        self._check_informal_reference(sources, target)

    def _upd_reference(self, table, field, sources, target, model_field=None, model=None):
        '''Update reference (field) to destination value (dst_id) where
        actual field value are in merging object ids (src_ids).
        if not constraint involve the field to update.
            Update all matching rows
        else
            check one by one if can update and update it or delete.

        '''
        constraints = self._get_contraints(table, field)
        if model_field:
            SUBQUERY = ["{field} = {id}", "{model_field}='{model}'"]
        else:
            SUBQUERY = ["{field} = '{model},{id}'"]
        if not constraints:
            if model_field:
                query = """UPDATE {table} SET {field}={target}
                               WHERE {field} IN ({filter})
                                  AND {model_field}='{model}';"""
                self._cr.execute(query.format(
                    table=table,
                    field=field,
                    target=target.id,
                    filter=','.join(str(i) for i in sources.ids),
                    model_field=model_field,
                    model=model
                ))
                return
            for record in sources:
                query = ("UPDATE {table} "
                         "SET {field}='{model},{target}' " +
                         "WHERE " + SUBQUERY[0])
                self._cr.execute(query.format(
                    table=table,
                    field=field,
                    model=model,
                    target=target.id,
                    id=record.id
                ))
            return
        else:
            query = ("SELECT {fields} FROM {table} WHERE " + ' AND '.join(SUBQUERY))
            for sources in sources:
                _query = (query.format(
                    fields=', '.join(str(i) for i in constraints[0]),
                    table=table,
                    field=field,
                    model=model,
                    id=sources.id,
                    model_field=model_field
                ))
                self._cr.execute(_query)
                for row in self._cr.dictfetchall():
                    filters = get_filters(row, field)
                    self._upd_del(
                        table,
                        field,
                        target,
                        filters,
                        sources.id,
                        model_field
                    )

    def _check_informal_reference(self, sources, target):
        for ref in self.env['informal.reference'].sudo().search([]):
            if self._check_field_exist(
                ref.table_name,
                (ref.id_field_name,
                 ref.model_field_name)):
                model = sources._name
                if ref.model_field_value == IS_MODEL_ID:
                    args = [('model', '=', model)]
                    model_id = IrModel.sudo().search(args)
                    if model_id:
                        self._upd_reference(
                            table=ref.table_name,
                            field=ref.id_field_name,
                            sources=sources,
                            target=target,
                            model_field=ref.model_field_name,
                            model=str(model_id.id)
                        )
                else:
                    self._upd_reference(
                        table=ref.table_name,
                        field=ref.id_field_name,
                        sources=sources,
                        target=target,
                        model_field=ref.model_field_name,
                        model=model
                    )

    def _check_field_exist(self, table_name, column_names):
        query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s AND column_name=%s
        """
        for column_name in column_names:
            self._cr.execute(query, (table_name, column_name))
            if not self._cr.rowcount:
                return False
            return True
