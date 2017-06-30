# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_web_notification.__openerp__
# ---------------------------------------------------------------------
# Copyright (c) 2016-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-04-19

{
    'name': 'Web Notifications',
    'version': '1.0',
    'category': 'Hidden',
    "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_web_notification",
    'depends': ['web', 'bus'],
    'data': [
        'view.xml',
    ],
    'qweb': ['static/src/xml/xopgi_web_notification.xml'],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': (8, 0) <= ODOO_VERSION_INFO < (9, 0),   # noqa

    'auto_install': True,
}
