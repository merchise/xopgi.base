#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_documents_share.__openerp__
# --------------------------------------------------------------------------
# Copyright (c) 2014-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.


{
    'name': 'Document Share in Purchases',
    'version': '1.0',
    'category': 'Knowledge',
    'description': ("Allows to share documents from a purchase order "
                    "to an invoice"),
    'author': 'Merchise Autrement',
    'website': '',
    'depends': ['base', 'purchase'],
    'data': [
        'view/document_share_view.xml',
    ],
    'installable': False,
    'auto_install': False,
}
