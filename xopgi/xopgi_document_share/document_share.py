#!/usr/bin/env python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------
# xopgi_document_share.document_share
#----------------------------------------------------------------------
# Copyright (c) 2014, 2015 Merchise Autrement and Contributors
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

    reference = fields.Reference(string='Model',
        selection='')

    @api.model
    def _reference_models(self):
        models = self.env['ir.model'].search([('osv_memory', '=', False)])
        return [(model.model, model.name)
                for model in models
                if not model.model.startswith('base.') and not
                model.model.startswith('base_')and
                not model.model.startswith('ir.')]

    @api.multi
    def action_share(self):
        try:
           for value in self:
              model = value.reference._name
              res_id = value.reference.id
              attachment_obj = self.env['ir.attachment']
              if model and res_id:
                 for active_id in self.env.context.get('active_ids', []):
                    parent_document = self.env['ir.attachment'].browse(
                        [ active_id])
                    attachment_obj = parent_document.copy({
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
