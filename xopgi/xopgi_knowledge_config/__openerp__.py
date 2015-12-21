#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_knowledge_config.__openerp__
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
    'name': 'Knowledge Config',
    'version': '1.0',
    'category': 'Knowledge Management',
    'description': """
    Module that allows to config documents
""",
    'author': 'Merchise Autrement',
    'website': '',
    'depends': ['base', 'knowledge'],
    'data': [
        'view/res_config_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': True,
}


