#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# res_users_v8
# ---------------------------------------------------------------------
# Copyright (c) 2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2017-07-18


from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)


from xoeuf import api
from xoeuf.models import Model

from xoeuf import MAJOR_ODOO_VERSION
assert MAJOR_ODOO_VERSION == 8


class User(Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        '''Create a new user record.

        In Odoo 8, if a user is created without using ``auth_crypt``, when you
        install this module, all passwords remains uncrypted until next time
        ``check_credentials`` is used.

        '''
        password = vals.pop('password', False)
        user = super(User, self).create(vals)
        if password:
            user.write({'password': password})
        return user
