# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_directory
# ---------------------------------------------------------------------
# Copyright (c) 2013-2015 Merchise Autrement
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-09-15

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
    "depends": ['base'],
    "data": [
        'views/res_partner_view.xml',
        'views/contact_reference_view.xml',
        'views/directory_config_view.xml',
        'data/res_partner_classification.xml',
        'wizards/make_fake_view.xml',
        'security/security.xml'

    ],
    "demo_xml": [],
    "application": False,
    "installable": True,
}
