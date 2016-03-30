#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_object_merge
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

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from openerp.release import version_info as ODOO_VERSION_INFO

if ODOO_VERSION_INFO < (9, 0):
    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.

    from . import work_distributor  # noqa
    from . import res_config  # noqa
