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
    'name': 'Sale Person board widget',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Create Sale Person board widget.

    """, "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_board",
    # FIXME:  Suspicious dependency on xopgi_operations_performance.
    'depends': ['xopgi_board', 'sale', 'xopgi_operations_performance'],
    'data': [
        'views/xopgi_board_view.xml',
        'views/xopgi_sale_view.xml',
        'data/sale_widgets.xml'
    ],
    'qweb': ['static/src/xml/xopgi_sale_board.xml'],
    'installable': True,
    'auto_install': True,
}
