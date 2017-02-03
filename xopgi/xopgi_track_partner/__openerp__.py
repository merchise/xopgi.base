#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# __openerp__
# ---------------------------------------------------------------------
# Copyright (c) 2017 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2017-01-26

{
    'name': 'Partner track visibility',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Define track visibility in res.partner fields.

    """,
    "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_track_partner",
    'depends': ['base', 'mail'],
    'data': ['data/partner_data.xml'],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': (8, 0) <= ODOO_VERSION_INFO < (9, 0),   # noqa

    'auto_install': False,
}
