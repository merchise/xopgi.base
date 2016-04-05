#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi.base._release
# ---------------------------------------------------------------------
# Copyright (c) 2013-2016 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_imports)


def read_terpfile():
    import os
    from os.path import join
    with open(join(os.path.dirname(__file__), '__openerp__.py'), 'rU') as fh:
        content = fh.read()
        # Odoo version doesn't really matter here.  But we need to provide a
        # fake one for the `eval` to succeed.
        fake = {'ODOO_VERSION_INFO': (7, 0)}
        return eval(content, fake, {})

_TERP = read_terpfile()
VERSION = _TERP['version']
