# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_stage_ext.__openerp__.py
# ---------------------------------------------------------------------
# Copyright (c) 2013-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#

{
    'name': 'Generic extension',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Create an abstract Model to use to extend stage model to set start and stop
flow.

    """,
    "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_crm_stage",
    'depends': ['base'],
    'data': [],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': 8 <= ODOO_VERSION_INFO[0] < 11,   # noqa

    'auto_install': True,
}
