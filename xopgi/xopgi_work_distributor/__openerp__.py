#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

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
