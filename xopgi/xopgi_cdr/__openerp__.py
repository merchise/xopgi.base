# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr.__openerp__
# ---------------------------------------------------------------------
# Copyright (c) 2016 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-02-13

{
    'name': 'Vigilant Base',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Create bases to allow system event management.

    """, "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_cdr",
    'depends': ['base'],
    'data': [
        'data/templates.xml',
        'views/control_variable_views.xml',
        'views/evidence_views.xml',
        'views/system_event_views.xml',
        'views/cdr_history_views.xml',
        'wizard/new_event_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
