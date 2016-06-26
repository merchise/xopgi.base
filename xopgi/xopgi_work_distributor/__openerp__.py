#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_work_distributor.__openerp__
# --------------------------------------------------------------------------
# Copyright (c) 2014, 2015, 2016 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# Author: Merchise Autrement [~º/~]
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.

{
    'name': 'Xopgi Work Distributor',
    'version': '1.0',
    'category': 'Tools',
    'description': """
    Generic automatic work distribution for any model
    """,
    'depends': ['base', 'web'],
    'data': [
        "security/security.xml",
        "view/res_config_view.xml",
        "view/work_distributor_view.xml",
        "data/work_distribution_strategies.xml",
    ],
    'demo': [],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': (8, 0) <= ODOO_VERSION_INFO < (9, 0),   # noqa

    'aplication': True,
}
