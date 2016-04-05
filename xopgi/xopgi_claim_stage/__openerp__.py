# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_claim_stage.__openerp__.py
# ---------------------------------------------------------------------
# Copyright (c) 2013-2016 Merchise Autrement
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-12-12

{
    'name': 'Extension for crm claim stage model',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Set start and stop flow fields to crm.claim.stage model.

    """, "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_claim_stage",
    'depends': ['xopgi_stage_ext', 'crm_claim'],
    'data': ['views/crm.xml'],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': (8, 0) <= ODOO_VERSION_INFO < (9, 0),   # noqa

    'auto_install': True,
}
