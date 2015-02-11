# -*- encoding: utf-8 -*-
# ----------------------------------------------------------------------
# post-001-update_lead_mobile_values
# ----------------------------------------------------------------------
# Copyright (c) 2015 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2015-02-11

'''Update mobile values on crm.lead

'''

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        unicode_literals as _py3_unicode,
                        absolute_import as _py3_abs_import)

from openerp import SUPERUSER_ID
from openerp.addons.crm.crm_lead import crm_lead as _base

from xoeuf.osv.orm import get_modelname
from xoeuf.osv.model_extensions import search_browse

from xoutil.modules import modulemethod


@modulemethod
def migrate(self, cr, version):
    from openerp.modules.registry import RegistryManager as manager
    self.pool = manager.get(cr.dbname)
    self.update_mobile(cr)


@modulemethod
def update_mobile(self, cr):
    lead_obj = self.pool[get_modelname(_base)]
    for lead in lead_obj.search_browse(cr, SUPERUSER_ID, domain=[],
                                       ensure_list=True):
        if not lead.mobile and lead.partner_id and lead.partner_id.mobile:
            lead_obj.write(cr, SUPERUSER_ID, lead.id,
                           {'mobile': lead.partner_id.mobile})
    return True
