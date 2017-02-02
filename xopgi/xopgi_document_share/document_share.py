#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_document_share.document_share
# ---------------------------------------------------------------------
# Copyright (c) 2014-2017 Merchise Autrement [~º/~] and Contributors
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
from openerp import SUPERUSER_ID


class Document(models.Model):
    _inherit = 'ir.attachment'

    owner = fields.Many2one(
        comodel_name='ir.attachment', string='Owner', required=False,
        ondelete='cascade')

    @api.multi
    def button_share(self):
        self.ensure_one()
        new_document = self.env['ir.attachment']
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ir.attachment.share',
            'res_id': new_document.id,
            'target': 'new',
        }


class DocumentShare(models.Model):
    _name = 'ir.attachment.share'

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

    @api.multi
    def action_share(self):
        try:
            for value in self:
                model = value.reference._name
                res_id = value.reference.id
                if model and res_id:
                    for active_id in self.env.context.get('active_ids', []):
                        parent_document = self.env['ir.attachment'].browse(
                            [active_id])
                        parent_document.copy({
                            'name': parent_document.name,
                            'user_id': parent_document.env.uid,
                            'res_id': res_id,
                            'res_model': model,
                            'owner': parent_document.id,
                        })
                else:
                    raise except_orm(_('Error!'),
                                     _('Check Model and Resourse Name'))

        except:
            raise except_orm(_('Error!'),
                             _('Check Model and Resourse Name'))
