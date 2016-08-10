# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_directory.wizards.make_fake
# ---------------------------------------------------------------------
# Copyright (c) 2013-2015 Merchise Autrement [~º/~]
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-09-30

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _absolute_import)


from openerp import api, exceptions, fields, models, _
from xoeuf.osv.orm import LINK_RELATED


class MakeFake(models.TransientModel):
    _name = 'make.fake'

    def get_contact_information(self):
        return self.env.context.get('active_ids', False)

    owner = fields.Many2one('res.partner', required=True)
    contact_information = fields.Many2many('res.partner', required=True,
                                           default=get_contact_information)

    @api.constrains('contact_information')
    def check_contact_information(self):
        if any(partner.contact_information
               for partner in self.contact_information):
            raise exceptions.ValidationError(
                _('Can\' make fake partners with related fake.'))

    @api.multi
    def confirm(self):
        self.contact_information.write({
            'fake': True,
            'owner': 'res.partner,%d' % self.owner.id,
            'user_ids': [LINK_RELATED(i.id) for i in self.owner.user_ids]
        })
        return self.owner.get_access_action()
