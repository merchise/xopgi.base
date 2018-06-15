#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

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
        "view/merger_view.xml",
        "data/know_informal_reference.xml",
        "data/predefine_field_merge_way.xml",
    ],
    'demo': [],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': 8 <= MAJOR_ODOO_VERSION < 11,   # noqa
    'application': True,
}
