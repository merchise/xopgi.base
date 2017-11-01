#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

dict(
    name='Mail integration merger',
    version='1.0',
    category='Hidden',
    author="Merchise Autrement",
    depends=['xopgi_object_merger', 'mail'],

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    installable= 8 <= MAJOR_ODOO_VERSION < 11,   # noqa

    auto_install=True,
)
