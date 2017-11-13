#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

{
    'name': 'Configuration dashboard widget',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Introduce dashboard widget configuration in the addons "xopgi_hr_contract".

    """, "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_board_widget",
    'depends': [
        'xopgi_hr_contract',
        'xopgi_board',
    ],
    'data': [
        'hr_job_view.xml',
    ],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': 8 <= MAJOR_ODOO_VERSION < 11,   # noqa

    'auto_install': True,
}
