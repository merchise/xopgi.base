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



from openerp.osv import fields, osv
from openerp.addons.object_merger.res_config import \
    object_merger_settings as _base

from xoeuf.osv.orm import get_modelname

DEFAULT_LIMIT_VALUE = 3

class object_merger_settings(osv.osv_memory):
    _name = get_modelname(_base)
    _inherit = _name

    def _get_objects_to_merge(self, cr, uid, ids, name, arg, context=None):
        obj = self.pool['ir.config_parameter']
        q = int(obj.get_param(cr, uid, 'objects_to_merge',
                              DEFAULT_LIMIT_VALUE, context=context))
        return {i: q for i in ids}

    def _set_objects_to_merge(self, cr, uid, _id, field_name, field_value,
                            arg, context=None):
        obj = self.pool['ir.config_parameter']
        return obj.set_param(cr, uid, 'objects_to_merge',
                             value=field_value or DEFAULT_LIMIT_VALUE,
                             context=context)

    _columns = {
        'limit':
            fields.function(
                _get_objects_to_merge, fnct_inv=_set_objects_to_merge,
                method=True, string='Object to merge limit', type='integer',
                help='Limit quantity of objects to allow merge at one time.'),
    }

    _defaults = {
        'limit': lambda self, cr, uid, c: (
            self._get_objects_to_merge(cr, uid, [0], None, None, context=c)[0]
        )
    }


    # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
