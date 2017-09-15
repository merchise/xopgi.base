# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.__openerp__.py
# ---------------------------------------------------------------------
# Copyright (c) 2013-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-10-29

{
    'name': 'Employee dashboard',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Create dashboard employee functions oriented.

    """, "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_board",
    'depends': [
        'hr',
        'web_calendar',
        'hr_contract',
    ],
    'data': [
        'views/xopgi_board_view.xml',
        'views/res_group_view.xml',
        'views/%d/hr_job_view.xml' % MAJOR_ODOO_VERSION,  # noqa
        'views/%d/xopgi_board_widget_view.xml' % MAJOR_ODOO_VERSION,  # noqa
        'views/%d/res_config_view.xml' % MAJOR_ODOO_VERSION,  # noqa
        'views/%d/assets.xml' % MAJOR_ODOO_VERSION,  # noqa
        'security/%d/security.xml' % MAJOR_ODOO_VERSION,  # noqa
    ],
    'qweb': ['static/src/xml/xopgi_board.xml'],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': 8 <= MAJOR_ODOO_VERSION < 11,   # noqa

    'auto_install': False,
}
