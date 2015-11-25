# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.__openerp__.py
# ---------------------------------------------------------------------
# Copyright (c) 2013-2015 Merchise Autrement
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
    # FIXME:  xopgi.base is supposed to provide the basis for other xopgi and
    # xhg modules, it's suspicious we depend on xopgi_hr_contract.
    'depends': ['web_kanban', 'xopgi_hr_contract'],
    'data': [
        'views/xopgi_board_view.xml',
        'views/hr_job_view.xml',
        'views/xopgi_board_widget_view.xml',
        'security/security.xml',
    ],
    'qweb': ['static/src/xml/xopgi_board.xml'],
    'installable': True,
    'auto_install': False,
}
