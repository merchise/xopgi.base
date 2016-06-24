# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_crm_stage.__openerp__.py
# ---------------------------------------------------------------------
# Copyright (c) 2013-2016 Merchise Autrement [~º/~]
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

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': (8, 0) <= ODOO_VERSION_INFO < (9, 0),   # noqa

    'auto_install': True,
}
