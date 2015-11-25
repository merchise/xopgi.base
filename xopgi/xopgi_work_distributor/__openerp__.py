#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_work_distributor.__openerp__
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
    'name': 'Xopgi Work Distributor',
    'version': '1.0',
    'category': 'Tools',
    'description': """
    Generic automatic work distribution for any model
    """,
    'depends': ['base'],
    'data': [
        "security/security.xml",
        "view/res_config_view.xml",
        "view/work_distributor_view.xml",
        "data/work_distribution_strategies.xml",
    ],
    'demo': [],
    'installable': True,
    'aplication': True,
}
