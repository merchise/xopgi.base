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

from openerp.osv.orm import Model

from xoeuf.osv.orm import get_modelname
from openerp.addons.crm.crm_lead import crm_lead as _base

class crm_lead(Model):
    _inherit = get_modelname(_base)

    def onchange_partner_id(self, cr, uid, ids, partner_id, email_from=False):
        _super = super(crm_lead, self).onchange_partner_id
        res = _super(cr, uid, ids, partner_id, email_from)
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            res['value']['mobile'] = partner.mobile
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
