# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_directory.contact_reference
# ---------------------------------------------------------------------
# Copyright (c) 2013-2015 Merchise Autrement
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-10-19

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _absolute_import)

from openerp import api, fields, models, _
from xoeuf import signals


class ContactReferenceModel(models.Model):
    _name = 'contact.reference.model'
    _description = 'Contact Reference Model'
    _rec_name = 'model'

    model = fields.Many2one('ir.model', required=True)
    fields_map = fields.One2many('contact.reference.field', 'ref_model',
                                 required=True)

    _sql_constraints = [
        ('model_unique', 'UNIQUE(model)',
         _("Only one contact reference per model are allowed."))
    ]

    @api.multi
    def get_contact(self, reference):
        return self.with_context(only_fake=True).env['res.partner'].search(
            [('owner', 'in', self.get_contact_identity(reference))])

    @api.one
    def get_contact_identity(self, reference):
        return '%s,%s' % (self.model.model, str(reference.id))

    @api.one
    @api.multi
    def sync_contact(self, action, reference, values=None):
        contact = self.get_contact(reference)
        if action == 'unlink':
            if contact:
                contact.unlink()
            return
        fields_map = self.fields_map.get_fields_map()
        contac_vals = {fields_map[f]: val
                       for f, val in values.iteritems()
                       if f in fields_map}
        if contac_vals:
            if not contact:
                action = 'create'
                contac_vals.update(
                    fake=True,
                    owner=self.get_contact_identity(reference)[0],
                )
            return getattr(contact, action)(contac_vals)


class ContactReferenceField(models.Model):
    _name = 'contact.reference.field'
    _description = 'Contact Reference Model Field'
    _rec_name = 'reference_field'

    reference_field = fields.Many2one('ir.model.fields', required=True)
    contact_field = fields.Many2one('ir.model.fields', required=True, domain=[
        ('ttype', 'in', ['char', 'text']),
        ('model', '=', 'res.partner')
    ])
    ref_model = fields.Many2one('contact.reference.model')
    model = fields.Many2one('ir.model', related='ref_model.model')

    _sql_constraints = [
        ('name_unique', 'UNIQUE(contact_field, ref_model)',
         _("Contact field must be unique per contact reference."))
    ]

    @api.multi
    def get_fields_map(self):
        result = {i.reference_field.name: i.contact_field.name for i in self}
        return result


@signals.receiver(signals.post_save)
def create_contact(self, signal, result, values=None):
    ''' Get contact reference configurations for model and apply it.

    '''
    contact_reference_model = self.env['contact.reference.model'].search(
        [('model.model', '=', self._name)])
    if contact_reference_model:
        contact_reference_model.sync_contact(signal.action, self or result,
                                             values)
    return True
