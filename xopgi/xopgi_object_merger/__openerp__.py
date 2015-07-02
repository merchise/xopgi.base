#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_object_merge.__openerp__
# --------------------------------------------------------------------------
# Copyright (c) 2014, 2015 Merchise Autrement and Contributors
# All rights reserved.
#
# Author: Merchise Autrement
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.

{
    'name': 'Xopgi Object Merger',
    'version': '1.0',
    'category': 'Tools',
    'description': """
    Generic merge option for any model
    """,
    'depends': ['base'],
    'data': [
        "view/res_config_view.xml",
        "view/object_merger_view.xml",
        "data/know_informal_reference.xml",
        "security/security.xml",
    ],
    'demo': [],
    'installable': True,
    'aplication': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
