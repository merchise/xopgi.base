#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_knowledge_config
# ---------------------------------------------------------------------
# Copyright (c) 2015 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#

from openerp.osv import fields, osv

class knowledge_config_settings(osv.osv_memory):
    _name = 'knowledge.config.settings'
    _inherit = 'knowledge.config.settings'
    _columns = {
        'module_xopgi_document_share': fields.boolean('Share documents'),
    }


