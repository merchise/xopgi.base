#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_crm_merge.crm_merge
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


from __future__ import (absolute_import as _py3_abs_imports,
                        division as _py3_division,
                        print_function as _py3_print,
                        unicode_literals as _py3_unicode)

from openerp.osv import fields, osv
from openerp import SUPERUSER_ID
from openerp.addons.crm.wizard.crm_merge_opportunities import \
    crm_merge_opportunity as base_crm_merge_opportunity
from xoeuf.osv.orm import get_modelname


class crm_merge_opportunity(osv.osv_memory):
    _name = get_modelname(base_crm_merge_opportunity)
    _inherit = _name

    def _check_quantity(self, cr, uid, ids, context=None):
        '''Check for groups_id of uid and if it are not sale manager check
        limit quantity of leads to merge.

        '''
        if uid == SUPERUSER_ID:
            return True
        pool = self.pool.get('ir.model.data')
        _, group_id = pool.get_object_reference(cr, uid, 'crm',
                                                'group_sale_manager')
        if group_id:
            user_data = self.pool['res.users'].read(cr, uid, uid,
                                                    ['groups_id'],
                                                    context=context)
            if user_data and group_id in user_data['groups_id']:
                return True
        obj = self.pool['ir.config_parameter']
        q = obj.get_param(cr, uid, 'leads_to_merge', 3, context=context)
        for merge in self.browse(cr, uid, ids, context=context):
            if merge.opportunity_ids and int(q) < len(merge.opportunity_ids):
                return False
        return True

    _constraints = [
        (_check_quantity,
         'You can`t merge so much opportunities at one time.',
         ['opportunity_ids']),
    ]