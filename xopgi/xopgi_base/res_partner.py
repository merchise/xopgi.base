# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_base.partner
# ---------------------------------------------------------------------
# Copyright (c) 2013-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2013-04-23

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        unicode_literals as _py3_unicode,
                        absolute_import as _absolute_import)


from xoutil.deprecation import deprecated

from openerp.osv.orm import Model
from openerp.osv import fields
import openerp.addons.base.res


# TODO: Deprecate and restructure all its uses
@deprecated(None, msg='Make "fax"" fields invisible in views.')
class res_partner(Model):
    '''A partner represents an entity that you do business with.

    That can be a prospect, a customer, a supplier, or even an employee of
    your company.

    In `XOPGI`, "fax" field is discarded because this concept is not used any
    more in modern world.

    `OpenERP` assumes that each new partner is a customer by default. This is
    ugly, but the only way to fix it is by modifying all usability scenarios
    (`OpenERP` views) in order to get a different value for each context. Also
    there are other classes of partners semantically in the same level of
    "customer" or "suplier" that must be included but it's difficult because
    these are boolean attributes.

    '''

    _name = openerp.addons.base.res.res_partner.res_partner._name
    _inherit = _name

    _columns = {
        'fax':
            fields.char('Fax', size=64, invisible=True)
        # TODO: There are other models that define the field "fax" -
        # "res.bank", "res.company", "crm.lead" and
        # "portal_crm.crm_contact_us".
    }

    # TODO: _defaults = {'customer': False}
