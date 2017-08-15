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
        'views/%d/assets.xml' % MAJOR_ODOO_VERSION, # noqa
    ],
    'qweb': [
        'static/src/xml/%d/xopgi_web_notification.xml' % MAJOR_ODOO_VERSION, # noqa
    ],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': 8 <= MAJOR_ODOO_VERSION < 11,   # noqa

    'auto_install': True,
}
