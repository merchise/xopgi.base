# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_base.res_user
# ---------------------------------------------------------------------
# Copyright (c) 2013-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2013-05-28

'''Extend ``res.user`` model.'''


from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _absolute_import)

from xoeuf import api
from xoeuf.models import Model


class User(Model):
    '''User class that extend `OpenERP` implementation.

    ``res.users`` inherits from ``res.partner``.  The partner model is used to
    store the data related to the partner: lang, name, address, avatar, ...
    The user model is dedicated to technical data.

    A ``res.users`` record models an `OpenERP` user and is different from an
    employee.

    '''

    _name = 'res.users'
    _inherit = _name

    @api.multi
    def deactivate(self):
        '''Deactivate users and all related partners.

        '''
        vals = {'active': False}
        self.write(vals)
        partners = self.mapped('partner_id').exists()
        partners.write(vals)
