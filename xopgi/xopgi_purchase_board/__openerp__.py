# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_purchase_board.__openerp__.py
# ---------------------------------------------------------------------
# Copyright (c) 2013-2015 Merchise Autrement
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-11-17

{
    'name': 'Purchaser board widget',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Create Purchaser board widget.

    """, "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_purchase_board",
    'depends': [
        'xopgi_coordination_board',
    ],
    'data': [
        'views/xopgi_purchase_view.xml',
        'data/purchase_widgets.xml'
    ],
    'qweb': ['static/src/xml/xopgi_purchase_board.xml'],
    'installable': True,
    'auto_install': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
