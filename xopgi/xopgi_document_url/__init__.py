#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_document_url
# ---------------------------------------------------------------------
# Copyright (c) 2016 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#

from __future__ import (absolute_import as _py3_abs_imports,
                        division as _py3_division,
                        print_function as _py3_print)

from openerp.release import version_info as ODOO_VERSION_INFO

if ODOO_VERSION_INFO < (9, 0):
    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.

    from . import wizard  # noqa
