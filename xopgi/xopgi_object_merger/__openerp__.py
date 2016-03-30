#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_object_merge.__openerp__
# --------------------------------------------------------------------------
# Copyright (c) 2014, 2015 Merchise Autrement and Contributors
# All rights reserved.
#
# Author: Merchise Autrement
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.

{
    'name': 'Xopgi Object Merger',
    'version': '1.0',
    'category': 'Tools',
    'description': """
    Generic merge option for any model
    """,
    'depends': ['base'],
    'data': [
        "view/res_config_view.xml",
        "view/object_merger_view.xml",
        "data/know_informal_reference.xml",
        "data/predefine_field_merge_way.xml",

        "security/security.xml",
    ],
    'demo': [],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': (8, 0) <= ODOO_VERSION_INFO < (9, 0),   # noqa

    'aplication': True,
}
