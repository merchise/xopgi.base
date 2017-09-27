# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_directory
# ---------------------------------------------------------------------
# Copyright (c) 2013-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#

{
    "name": "XOPGI Directory",
    "version": "1.0",
    "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_res_partner",
    "category": "Hidden",
    "summary": "Merchise Extension for Institutional Directory.",
    "description": """
    Extension of res.partner to improve the contact management on odoo.
    """,
    "depends": [
        'base',
        'mail',
        'contacts'
    ],
    "data": [
        'views/%d/res_partner_view.xml' % ODOO_VERSION_INFO[0],   # noqa
        'views/%d/res_partner_classification_view.xml' % ODOO_VERSION_INFO[0],   # noqa
        'data/res_partner_classification.xml',
        'wizards/%d/make_fake_view.xml' % ODOO_VERSION_INFO[0],   # noqa
        'security/security.xml'

    ],
    "demo_xml": [],
    "application": False,

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': 8 <= ODOO_VERSION_INFO[0] < 11,   # noqa

}
