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
    'depends': ['xopgi_board', 'sale'],
    'data': [
        'views/xopgi_board_view.xml',
        'views/xopgi_sale_view.xml'
    ],
    'qweb': ['static/src/xml/xopgi_sale_board.xml'],
    'installable': True,
    'auto_install': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
