# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_directory.res_partner
# ---------------------------------------------------------------------
# Copyright (c) 2013-2015 Merchise Autrement
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-09-15

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _absolute_import)


from openerp import api, fields, models
from xoeuf.osv.orm import FORGET_RELATED, LINK_RELATED


@api.multi
def get_contact_information(self):
    """ Get fake partners related with given objects.

    """
    return self.env['res.partner'].with_context(only_fake=True).search(
        [('owner', 'in', list({'%s,%d' % (self._name, i.id) for i in self}))])


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.one
    @api.depends('owner')
    def _get_owner_identity(self):
        if self.owner:
            _, name = self.owner.get_name()[0]
            self.owner_identity = '%s: %s' % (self.owner._name, name)
        else:
            self.owner_identity = ''

    @api.one
    def _get_fake_partners(self):
        """If self is fake then get all fake partners with same owner of
        self else get all fake partners with owner is self.

        """
        if self.fake:
            owner = self.owner
        else:
            owner = self
        self.contact_information = get_contact_information(owner)

    fake = fields.Boolean()
    owner = fields.Reference(selection=[])
    owner_identity = fields.Char(compute='_get_owner_identity')
    contact_information = fields.One2many('res.partner',
                                          compute='_get_fake_partners')
    classifications = fields.Many2many('res.partner.classification',
                                       'res_partner_classification_rel',
                                       'partner_id', 'classification_id')
    employee = fields.Boolean(
        compute='_get_classification',
        inverse=lambda self: self._set_classification('employee'), store=True)
    customer = fields.Boolean(
        compute='_get_classification',
        inverse=lambda self: self._set_classification('customer'), store=True)
    supplier = fields.Boolean(
        compute='_get_classification',
        inverse=lambda self: self._set_classification('supplier'), store=True)

    @api.one
    @api.depends('classifications')
    def _get_classification(self):
        c_ids = self.classifications.ids
        ref = lambda xml_id: self.env.ref(xml_id, raise_if_not_found=False)
        for att in ('employee', 'customer', 'supplier'):
            classific = ref('xopgi_directory.%s' % att)
            setattr(self, att,
                    True if classific and classific.id in c_ids else False)

    def _set_classification(self, classification):
        ref = lambda xml_id: self.env.ref(xml_id, raise_if_not_found=False)
        classific = ref('xopgi_directory.%s' % classification)
        if classific:
            action = (LINK_RELATED if getattr(self, classification, False)
                      else FORGET_RELATED)
            self.write({'classifications': [action(classific.id)]})

    @api.model
    def _where_calc(self, domain, active_test=True):
        domain = domain if domain else []
        if self._context.get('only_fake', False):
            if not any(item[0] == 'fake' for item in domain):
                domain.insert(0, ('fake', '=', True))
        elif not self._context.get('include_fake', False):
            if not any(item[0] == 'fake' for item in domain):
                domain.insert(0, ('fake', '=', False))
        return super(ResPartner, self)._where_calc(
            domain, active_test=active_test)

    @api.model
    def migrate_classifications(self):
        """This is needed because a migration not occur on module installation.

        """
        ref = lambda xml_id: self.env.ref(xml_id, raise_if_not_found=False)
        partners = self.with_context(active_test=False)
        for att in ('employee', 'customer', 'supplier'):
            partners = partners.search([(att, '=', True)])
            classification = ref('xopgi_directory.%s' % att)
            if partners and classification:
                partners.write(
                    {'classifications': [LINK_RELATED(classification.id)]})


class PartnerClassification(models.Model):
    _name = 'res.partner.classification'

    name = fields.Char(required=True, translate=True)
    partners = fields.Many2many('res.partner',
                                'res_partner_classification_rel',
                                'classification_id', 'partner_id')
