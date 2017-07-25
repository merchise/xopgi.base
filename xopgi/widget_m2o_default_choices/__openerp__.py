#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# __openerp__
# ---------------------------------------------------------------------
# Copyright (c) 2016-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-02-04

{
    'name': 'Many2One Default Choices Widget',
    'category': 'Hidden',
    'version': '1.0',
    'depends': ['web'],
    'data': [
        'views/%d/many2one_default_choices.xml' % MAJOR_ODOO_VERSION,
    ],
    'auto_install': False,

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': 8 <= MAJOR_ODOO_VERSION < 11,   # noqa

}
