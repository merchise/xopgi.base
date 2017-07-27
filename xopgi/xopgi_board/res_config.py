# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.res_config
# ---------------------------------------------------------------------
# Copyright (c) 2014-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoeuf import models, fields


def BoardValue(xml_id, model, module, **kwargs):
    '''A board value field.

    A value is a M2O field stored like as an XML_ID of the `model` and
    `module` provided.

    To be used within the model 'xopgi.board.config' to introduce further
    values or configuration.

    '''
    module = module.rsplit('.', 1)[-1]  # Allow module to be fully qualified
                                        # so you can say __name__  # noqa
    return fields.Many2one(
        model,
        compute=lambda self: self._compute_value(xml_id, module=module),
        inverse=lambda self: self._set_value(xml_id, model, module=module),
        default=lambda self: self._compute_value(xml_id, module=module),
        **kwargs
    )


class XopgiBoardConfig(models.TransientModel):
    '''A base for all configurations of the Board.'''
    _name = 'xopgi.board.config'
    _inherit = 'res.config.settings'

    def _compute_value(self, xml_id, module):
        '''A simple method that computes a value from a XML_ID.

        Use

        '''
        xmlid = '%s.%s' % (module, xml_id)
        result = self.env.ref(xmlid, raise_if_not_found=False)
        for item in self:
            setattr(item, xml_id, result or False)
        return result or False

    def _set_value(self, xml_id, model, module):
        variable = getattr(self, xml_id, None)
        if variable:
            model_data = self.env['ir.model.data'].search(
                [('module', '=', module),
                 ('name', '=', xml_id),
                 ('model', '=', model)],
                limit=1
            )
            if model_data:
                model_data.res_id = variable.id
            else:
                model_data.create(dict(module=module, xml_id=xml_id,
                                       model=model, res_id=variable.id))
