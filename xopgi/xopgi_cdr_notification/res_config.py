# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.res_config
# ---------------------------------------------------------------------
# Copyright (c) 2014 - 2016 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-01-23

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from openerp import fields, models
from openerp.tools.safe_eval import safe_eval

TEMPLATES = [
    ('info_notification_template', 'Information'),
    ('alert_notification_template', 'Alert'),
    ('alarm_notification_template', 'Alarm')
]


class XopgiCDRNotificationConfig(models.TransientModel):
    _name = 'xopgi.cdr.notification.config'
    _inherit = 'res.config.settings'

    def _get_template(self):
        res = {}
        for param, _ in TEMPLATES:
            res[param] = self.get_res_id(param).id
        self.write(res)

    def _set_template(self):
        for item in self:
            for param, _ in TEMPLATES:
                self.env['ir.config_parameter'].set_param(
                    param, str(getattr(item, param).id))

    info_notification_template = fields.Many2one(
        'email.template', compute='_get_template', inverse='_set_template',
        default=lambda self: self.get_res_id(TEMPLATES[0][0]))

    alert_notification_template = fields.Many2one(
        'email.template', compute='_get_template', inverse='_set_template',
        default=lambda self: self.get_res_id(TEMPLATES[1][0]))

    alarm_notification_template = fields.Many2one(
        'email.template', compute='_get_template', inverse='_set_template',
        default=lambda self: self.get_res_id(TEMPLATES[2][0]))

    def get_res_id(self, xml_id):
        param_value = safe_eval(
            str(self.env['ir.config_parameter'].get_param(xml_id)))
        if param_value:
            return param_value
        else:
            default_value = self.env.ref(
                'xopgi_cdr_notification.%s' % xml_id,
                raise_if_not_found=False)
            return default_value.id if default_value else False
