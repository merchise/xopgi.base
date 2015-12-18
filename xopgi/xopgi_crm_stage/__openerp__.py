# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_crm_stage.__openerp__.py
# ---------------------------------------------------------------------
# Copyright (c) 2013-2015 Merchise Autrement
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-12-12

{
    'name': 'Extension for crm stage model',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Set start and stop flow fields to crm.stage model.

    """,
    "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_crm_stage",
    'depends': ['xopgi_stage_ext', 'crm'],
    'data': ['views/crm.xml'],
    'installable': True,
    'auto_install': True,
}
