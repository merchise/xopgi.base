#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_web_flexlist
# ---------------------------------------------------------------------
# Copyright (c) 2015 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2015-02-24

dict(
    name="Web Many2Many Flexlist",
    version="1.0",
    summary="Introduces a widget 'many2many_flexlist' that ",
    author="Merchise Autrement and Contributors",
    website="",
    category="Generic Widget",
    description="""
Web Many2Many Flexlist
======================

Adds a widget "many2many_flexlist" that allows to either choose an exiting
item or create one inline, effectively mixing the behavior of the "many2many"
and "one2many" widget.

    """,
    depends=['web', ],
    js=['static/src/js/flexlist.js', ],
    qweb=['static/src/xml/flexlist.xml', ],
    auto_install=True,
    application=False,
    installable=True,
)
