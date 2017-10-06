#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# __openerp__
# ---------------------------------------------------------------------
# Copyright (c) 2017 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2017-01-26

dict(
    name='Mail integration merger',
    version='1.0',
    category='Hidden',
    author="Merchise Autrement",
    depends=['xopgi_object_merger', 'mail'],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    installable= 8 <= MAJOR_ODOO_VERSION < 9,   # noqa

    auto_install=True,
)
