#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_work_distributor.__openerp__
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
    'name': 'Xopgi Work Distributor',
    'version': '1.1',
    'category': 'Tools',
    'description': """
    Generic automatic work distribution for any model
    """,
    'depends': ['base', 'web'],
    'data': [
        "security/security.xml",
        "view/%d/res_config_view.xml" % ODOO_VERSION_INFO[0],  # noqa
        "view/work_distributor_view.xml",
        "data/work_distribution_strategies.xml",
    ],
    'demo': [],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': 8 <= ODOO_VERSION_INFO[0] < 11,   # noqa

    'aplication': True,
}
