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

from openerp.osv import orm, osv

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


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
