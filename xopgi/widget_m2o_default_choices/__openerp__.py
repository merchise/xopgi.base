#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# __openerp__
# ---------------------------------------------------------------------
# Copyright (c) 2016 Merchise Autrement [~º/~] and Contributors
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
    'description': """
Many2One Default Choices Widget.
================================

Allow define a domain in many2one fields to establish choices as defaults.
Usage:
    <field name="many2one_fieldname"
           widget="many2one_default_choices"
           priority_domain="as_domain_attribute"/>

""",
    'version': '1.0',
    'depends': ['web'],
    'data': [
        'views/many2one_default_choices.xml',
    ],
    'auto_install': False,

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': (8, 0) <= ODOO_VERSION_INFO < (9, 0),   # noqa

}
