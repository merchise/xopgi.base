#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_crm_merge.res_config
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
from openerp.addons.crm.res_config import crm_configuration as base_crm_configuration

from xoeuf.osv.orm import get_modelname

DEFAULT_LIMIT_VALUE = 3

class crm_configuration(osv.osv_memory):
    _name = get_modelname(base_crm_configuration)
    _inherit = _name

    def _get_leads_to_merge(self, cr, uid, ids, name, arg, context=None):
        obj = self.pool['ir.config_parameter']
        q = obj.get_param(cr, uid, 'leads_to_merge', DEFAULT_LIMIT_VALUE,
                          context=context)
        return {i: q for i in ids}

    def _set_leads_to_merge(self, cr, uid,_id, field_name, field_value,
                            arg, context=None):
        obj = self.pool['ir.config_parameter']
        return obj.set_param(cr, uid, 'leads_to_merge',
                             value=field_value or DEFAULT_LIMIT_VALUE,
                             context=context)

    _columns = {
        'leads_to_merge':
            fields.function(_get_leads_to_merge,
                            fnct_inv=_set_leads_to_merge, method=True,
                            string='Leads to merge limit',
                            type='integer',
                            help = 'Limit quantity of leads to allow merge '
                                   'at one time.'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
