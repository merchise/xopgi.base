# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr_notification.__openerp__
# ---------------------------------------------------------------------
# Copyright (c) 2016 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-03-07

{
    'name': 'Vigilant Notifications handler',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Create a basic event based notification system.

    """,
    "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_cdr_notification",
    'depends': ['web', 'xopgi_cdr', 'im_chat', 'xopgi_web_notification'],
    'data': [
        'data/vigilant_user.xml',
        'security/security.xml',
        'views/event_handler_views.xml',
        'views/res_users_views.xml',
    ],
    'qweb': [],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': (8, 0) <= ODOO_VERSION_INFO < (9, 0),   # noqa

    'auto_install': True,
}
