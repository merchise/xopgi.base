#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_documents_share_all.__openerp__
# --------------------------------------------------------------------------
# Copyright (c) 2014, 2015 Merchise Autrement and Contributors
# All rights reserved.
#
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.


{
    'name': 'Document Share All',
    'version': '1.0',
    'category': 'Knowledge',
    'description': "Allows to share documents from any model "
                    "to any model",
    'author': 'Merchise Autrement',
    'website': '',
    'depends': ['base','mail'],
    'data': [
        'view/document_share_view.xml',
    ],
    'js': ['static/src/js/share.js'],
    'qweb': [
        'static/src/xml/share.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}


