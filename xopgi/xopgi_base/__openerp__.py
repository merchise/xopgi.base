# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_base
# ---------------------------------------------------------------------
# Copyright (c) 2013-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2013-04-09

{
    "name": "XOPGI Base",
    "version": "1.5",
    "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_base",
    "category": "Hidden",
    "summary": "Merchise Extension of OpenERP Kernel",
    "description": """
Extensions to `OpenERP` kernel for all dependant XOPGI components
=================================================================

`XOPGI` include all general Merchise 'OpenERP'' addons.

The name *XOPGI* comes from *Progiciel Libre de Gestion Intégré*, in french
"Free Software for Integrated Management". The word "Libre" is changed for
"Open". The term is similar to `OpenERP` in french.

This module never will be installed manually, it will be used automatically
for all XOPGI's dependant components.

""",
    "depends": ['base'],
    "data": [
        'view/%d/xopgi_security.xml' % MAJOR_ODOO_VERSION,  # noqa
        'view/%d/xopgi_model_view.xml' % MAJOR_ODOO_VERSION,  # noqa
    ],
    "demo_xml": [],
    "application": False,

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': 8 <= MAJOR_ODOO_VERSION < 11,   # noqa
}
