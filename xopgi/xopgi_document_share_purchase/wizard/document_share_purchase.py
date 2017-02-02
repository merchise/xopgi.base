#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_document_share.document_share
# ---------------------------------------------------------------------
# Copyright (c) 2015-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#

from __future__ import (absolute_import as _py3_abs_imports,
                        division as _py3_division,
                        print_function as _py3_print)
from openerp import api, models, fields, _
from openerp.exceptions import except_orm
from openerp.osv.orm import TransientModel


class Document(models.Model):
    _inherit = 'ir.attachment'

    owner = fields.Many2one(
        comodel_name='ir.attachment', string='Owner', required=False,
        ondelete='cascade')


class DocumentShare(TransientModel):
    _name = 'purchase.order.share'

    @api.model
    def _get_attachment(self):
        for active_id in self.env.context.get('active_ids', []):
            domain = [('res_model', '=', 'purchase.order'),
                      ('res_id', '=', active_id)]
            attachments = self.env['ir.attachment'].search(domain)
            return attachments

    reference = fields.Many2one(comodel_name='account.invoice',
                                string="Invoice",
                                domain=[('state', '!=', 'cancel')])
    attachments = fields.Many2many(
        comodel_name='ir.attachment', string='Attachments',
        relation='ir_attachment_rel', column1='order_id',
        column2='document_id', domain=[('res_model', '=', 'purchase.order')],
        default=_get_attachment)
    _defaults = {
        'attachments': _get_attachment,
    }

    @api.multi
    def action_share(self):
        try:
            for value in self:
                model = 'account.invoice'
                res_id = value.reference.id
                if res_id:
                    for att in value.attachments:
                        att.copy({
                            'name': att.name,
                            'user_id': att.env.uid,
                            'res_id': res_id,
                            'res_model': model,
                            'owner': att.id,
                        })
                else:
                    raise except_orm(_('Error!'),
                                     _('Check Model and Resourse Name'))

        except:
            raise except_orm(_('Error!'),
                             _('Check Model and Resourse Name'))
