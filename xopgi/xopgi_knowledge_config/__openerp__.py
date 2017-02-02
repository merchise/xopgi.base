#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_knowledge_config.__openerp__
# --------------------------------------------------------------------------
# Copyright (c) 2014-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.


{
    'name': 'Knowledge Config',
    'version': '1.0',
    'category': 'Knowledge Management',
    'description': "Allows to config documents",
    'author': 'Merchise Autrement',
    'website': '',
    'depends': ['base', 'knowledge'],
    'data': [
        'view/res_config_view.xml',
    ],
    'demo': [],
    'test': [],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': (8, 0) <= ODOO_VERSION_INFO < (9, 0),   # noqa

    'auto_install': True,
}
