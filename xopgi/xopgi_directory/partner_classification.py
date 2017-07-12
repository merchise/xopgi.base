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


from xoeuf import api, fields, models
from xoeuf.osv.orm import FORGET_RELATED, LINK_RELATED


EMPLOYEE_CLASSIFIER_XMLID = 'xopgi_directory.employee'
CUSTOMER_CLASSIFIER_XMLID = 'xopgi_directory.customer'
SUPPLIER_CLASSIFIER_XMLID = 'xopgi_directory.supplier'
PROVIDER_CLASSIFIER_XMLID = SUPPLIER_CLASSIFIER_XMLID


STANDARD_CLASSIFIERS = (
    EMPLOYEE_CLASSIFIER_XMLID,
    CUSTOMER_CLASSIFIER_XMLID,
    SUPPLIER_CLASSIFIER_XMLID,
)

ATTR2CLASSIFIER_MAPPING = dict(
    employee=EMPLOYEE_CLASSIFIER_XMLID,
    supplier=SUPPLIER_CLASSIFIER_XMLID,
    customer=CUSTOMER_CLASSIFIER_XMLID,
)


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
        classes_ids = self.classifications.ids
        ref = lambda xml_id: self.env.ref(xml_id, raise_if_not_found=False)
        for attr, classname in ATTR2CLASSIFIER_MAPPING.items():
            classific = ref(classname)
            setattr(self, attr, classific.id in classes_ids)

    def _set_classification(self, attrname):
        ref = lambda xml_id: self.env.ref(xml_id, raise_if_not_found=False)
        classific = ref(ATTR2CLASSIFIER_MAPPING.get(attrname, 'null'))
        if classific:
            if getattr(self, attrname, False):
                self.write({'classifications': [LINK_RELATED(classific.id)]})
            else:
                self.write({'classifications': [FORGET_RELATED(classific.id)]})

    @api.model
    def migrate_classifications(self):
        """This is needed because a migration not occur on module installation.

        """
        ref = lambda xml_id: self.env.ref(xml_id, raise_if_not_found=False)
        partners = self.with_context(active_test=False)
        for attr, classname in ATTR2CLASSIFIER_MAPPING.items():
            partners = partners.search([(attr, '=', True)])
            classification = ref(classname)
            if partners and classification:
                partners.write(
                    {'classifications': [LINK_RELATED(classification.id)]}
                )


class PartnerClassification(models.Model):
    _name = 'res.partner.classification'

    name = fields.Char(required=True, translate=True)
    partners = fields.Many2many(
        'res.partner',
        'res_partner_classification_rel',
        'classification_id',
        'partner_id'
    )
