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
                        unicode_literals as _py3_unicode,
                        absolute_import as _absolute_import)

from xoeuf import ODOO_VERSION_INFO
assert ODOO_VERSION_INFO[0] == 8


from openerp.osv.orm import Model
import openerp.addons.base.res


class res_users(Model):
    '''User class that extend `OpenERP` implementation.

    ``res.users`` inherits from ``res.partner``.  The partner model is used to
    store the data related to the partner: lang, name, address, avatar, ...
    The user model is dedicated to technical data.

    A ``res.users`` record models an `OpenERP` user and is different from an
    employee.

    '''

    _name = openerp.addons.base.res.res_users.res_users._name
    _inherit = _name

    def create(self, cr, uid, vals, context=None):
        '''Create a new user record.

        .. note:: See :py:meth:`~osv.orm.Model.create` method for more
           details.

        In `OpenERP`, if a user is created without using ``auth_crypt``, when
        you install this module, all passwords remains uncrypted until next
        time ``check_credentials`` is used.

        '''
        password = vals.pop('password', False)
        user_id = super(res_users, self).create(cr, uid, vals, context=context)
        if password:
            self.write(cr, uid, user_id, {'password': password}, context=context)
        return user_id

    def deactivate(self, cr, uid, ids, context=None):
        '''Deactivate users and all related partners.

        :param cr: database cursor

        :param uid: current user id

        :type user: integer

        :param ids: user ids to be deactivated

        :param context: (optional) context arguments

        :type context: dictionary

        '''
        # TODO: [med] This method is only used in migration tools, maybe its
        # functionality must be moved outside add-ons code.  Programmed by
        # ~Yurdik.
        if isinstance(ids, (int, long)):
            ids = [ids]
        vals = {'active': False}
        res = self.write(cr, uid, ids, vals, context=context)
        pids = [u.partner_id.id for u in self.browse(cr, uid, ids, context=context)]
        partner_obj = self.pool['res.partner']
        partner_obj.write(cr, uid, pids, vals, context=context)
        return res
