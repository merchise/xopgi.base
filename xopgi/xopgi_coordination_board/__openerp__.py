# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_coordination_board.__openerp__.py
# ---------------------------------------------------------------------
# Copyright (c) 2013-2015 Merchise Autrement
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-11-14

{
    'name': 'Coordinator board widget',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Create Coordinator board widget.

    """, "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_coordination_board",
    'depends': [
        'xopgi_sale_board',
        'xhg_autrement_project_dossier',
        'xhg_autrement_purchase_business_adapter',
    ],
    'data': [
        'views/xopgi_coordination_view.xml',
        'data/coordination_widgets.xml'
    ],
    'qweb': ['static/src/xml/xopgi_coordination_board.xml'],
    'installable': True,
    'auto_install': True,
}
