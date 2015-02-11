#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_crm_merge.__openerp__
# --------------------------------------------------------------------------
# Copyright (c) 2014, 2015 Merchise Autrement and Contributors
# All rights reserved.
#
# Author: Merchise Autrement
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.


{
    'name': 'XOPGI_crm_merge',
    'version': '1.2',
    'author': 'Merchise Autrement',
    'category': 'Hidden',
    'application': False,
    'installable': True,
    'summary': 'Add leads merge restrictions.',
    'depends': ['crm'],
    'data': [
        'view/res_config_view.xml',
        'data/defaults.xml'
    ],
}
