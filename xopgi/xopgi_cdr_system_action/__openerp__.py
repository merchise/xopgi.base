# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr_system_action.__openerp__
# ---------------------------------------------------------------------
# Copyright (c) 2016 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-04-10

{
    'name': 'Vigilant Server Action handler',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Allow to create cdr event handlers to execute server actions.

    """, "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_cdr_system_action",
    'depends': ['xopgi_cdr'],
    'data': [
        'security/security.xml',
        'views/event_handler_views.xml',
    ],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': (8, 0) <= ODOO_VERSION_INFO < (9, 0),   # noqa
}
