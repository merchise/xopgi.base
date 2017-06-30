# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr.__openerp__
# ---------------------------------------------------------------------
# Copyright (c) 2016-2017 Merchise Autrement [~º/~] and Contributors
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
    "author": "Merchise Autrement",
    "website": "http://xhg.ca.merchise.org/addons/xopgi_cdr",
    'depends': ['base', 'xopgi_recurrence'],
    'data': [
        'security/security.xml',
        'data/cron.xml',
        'data/templates.xml',
        'views/control_variable_views.xml',
        'views/evidence_views.xml',
        'views/system_event_views.xml',
        'views/cdr_history_views.xml',
        'wizard/new_event_views.xml',
    ],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': (8, 0) <= ODOO_VERSION_INFO < (9, 0),   # noqa

    'auto_install': False,
}
