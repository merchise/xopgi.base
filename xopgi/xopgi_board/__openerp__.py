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
    'depends': ['hr', 'web_calendar', 'xopgi_hr_contract'],
    'data': [
        'views/xopgi_board_view.xml',
        'views/hr_job_view.xml',
        'views/res_group_view.xml',
        'views/xopgi_board_widget_view.xml',
        'views/res_config_view.xml',
        'security/security.xml',
    ],
    'qweb': ['static/src/xml/xopgi_board.xml'],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': (8, 0) <= ODOO_VERSION_INFO < (9, 0),   # noqa

    'auto_install': False,
}
