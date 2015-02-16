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

from openerp.addons.object_merger.wizard.object_merger \
    import object_merger as _base

from xoeuf.osv.orm import get_modelname


class object_merger(orm.TransientModel):
    _inherit = get_modelname(_base)

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
                                                         submenu=False)
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
        """Check if any of merged object_ids are referenced on any mail.alias
        and on this case update the references to the destination object_id
        """
        res = super(object_merger, self).action_merge(cr, uid, ids, context=context)
        active_model = context.get('active_model')
        object_ids = context.get('active_ids', [])
        field_to_read = context.get('field_to_read')
        object = self.read(cr, uid, ids[0], [field_to_read], context=context)
        object_id = object[field_to_read][0]
        query = """SELECT id, alias_defaults FROM mail_alias
                 WHERE alias_model_id = {model}
                 AND (alias_defaults LIKE '%''{field}''%')"""
        cr.execute(
            "SELECT name, model, model_id, ttype FROM ir_model_fields WHERE "
            "relation=%s;",
            (active_model, )
        )
        read = cr.fetchall()
        for field, model, model_id, ttype in read:
            pool = self.pool[model]
            if hasattr(pool, '_columns'):
                col = pool._columns[field]
                if isinstance(col, fields.many2one):
                    cr.execute(query.format(model=model_id, field=field))
                    for alias, defaults in cr.fetchall():
                        try:
                            defaults = dict(eval(defaults))
                            val = defaults[field]
                            if val in object_ids and val != object_id:
                                defaults[field] = object_id
                                upd = self.pool['mail.alias'].write
                                vals = {'alias_defaults': str(defaults)}
                                upd(cr, SUPERUSER_ID, alias, vals, context=context)
                        except Exception:
                            pass
                # TODO: tambien hay que darle tratamiento a los one2many y
                # many2many

                # TODO: refactorizar el módulo original para liminar el
                # error de violación de restricciones en la BD.
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
