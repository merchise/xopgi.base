# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_recurrence.__openerp__
# ---------------------------------------------------------------------
# Copyright (c) 2016-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-05-12

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
