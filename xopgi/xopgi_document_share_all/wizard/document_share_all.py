#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_documents_share_all.document_share_all
# ---------------------------------------------------------------------
# Copyright (c) 2014, 2015, 2016 Merchise Autrement [~º/~] and Contributors
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
from openerp import SUPERUSER_ID


class Document(models.Model):
    _inherit = 'ir.attachment'

    owner = fields.Many2one(
        comodel_name='ir.attachment', string='Owner', required=False,
        ondelete='cascade')


class DocumentShare(TransientModel):
    _name = 'ir.attachment.share.all'

    @api.model
    def _get_attachment(self):
        for active_id in self.env.context.get('active_ids', []):
            active_model = self.env.context.get('active_model')
            domain = [('res_model', '=', active_model),
                      ('res_id', '=', active_id)]
            attachments = self.env['ir.attachment'].search(domain)
            return attachments

    def _get_model_selection(self, cr, uid, context=None):
        thread_obj = self.pool['mail.thread']

        def check(model):
            try:
                return self.pool[model].search(
                    cr, uid, [], limit=1, context=context, count=True)
            except:
                return False

        translate = lambda source: (
            self.pool['ir.translation']._get_source(
                cr, SUPERUSER_ID, None, ('model',),
                (context or {}).get('lang', False), source) or source)
        models = [
            (n, translate(d)) for n, d in thread_obj.message_capable_models(
                cr, uid, context=context).items()
            if (n != 'mail.thread' and check(n))]
        return models

    reference = fields.Reference(
        string='Model',
        selection='_get_model_selection'
    )

    attachments = fields.Many2many(
        comodel_name='ir.attachment', string='Attachments',
        relation='ir_attachment_rel',
        column1='order_id',
        column2='document_id',
        default=_get_attachment)

    @api.multi
    def action_share(self):
        try:
            for value in self:
                model = value.reference._name
                res_id = value.reference.id
                if model and res_id:
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
