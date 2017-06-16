# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_directory.res_partner
# ---------------------------------------------------------------------
# Copyright (c) 2013-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _absolute_import)


from openerp import api, fields, models
from xoeuf.osv.orm import FORGET_RELATED, LINK_RELATED


class ResPartner(models.Model):
    _inherit = 'res.partner'

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
