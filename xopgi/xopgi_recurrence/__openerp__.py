#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

{
    'name': "xopgi_recurrence",
    'summary': """Basic definition for recurrence""",
    'category': 'Hidden',
    "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_recurrence",
    'version': '1.0',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
    ],

    'installable': 8 <= ODOO_VERSION_INFO[0] < 11,  # noqa
}
