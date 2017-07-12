# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_directory
# ---------------------------------------------------------------------
# Copyright (c) 2013-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)


from xoeuf import ODOO_VERSION_INFO

if 8 <= ODOO_VERSION_INFO[0] < 11:
    from . import partner_classification  # noqa
