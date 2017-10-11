#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_object_merge.__openerp__
# --------------------------------------------------------------------------
# Copyright (c) 2014-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# Author: Merchise Autrement [~º/~]
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.

{
    'name': 'Xopgi Object Merger',
    'version': '1.0',
    'category': 'Tools',
    'depends': ['base'],
    'data': [
        "security/security.xml",
        "view/res_config_view.xml",
        "view/%d/menu.xml" % MAJOR_ODOO_VERSION, # noqa
        "view/object_merger_view.xml",
        "data/know_informal_reference.xml",
        "data/predefine_field_merge_way.xml",
    ],
    'demo': [],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': 8 <= MAJOR_ODOO_VERSION < 9,   # noqa
    'application': True,
}
