#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_documents_share.__openerp__
# --------------------------------------------------------------------------
# Copyright (c) 2014, 2015, 2016 Merchise Autrement and Contributors
# All rights reserved.
#
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.


{
    'name': 'Document Share',
    'version': '1.0',
    'category': 'Knowledge Management',
    'description': "Allows to share documents",
    'author': 'Merchise Autrement',
    'website': '',
    'depends': ['base', 'knowledge'],
    'data': [
        'view/document_share_view.xml',
        'security/ir.model.access.csv',
        'security/security.xml'
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
