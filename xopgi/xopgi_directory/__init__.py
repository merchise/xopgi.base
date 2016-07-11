# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_directory
# ---------------------------------------------------------------------
# Copyright (c) 2013-2016 Merchise Autrement [~º/~]
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-09-15

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from openerp.release import version_info as ODOO_VERSION_INFO

if ODOO_VERSION_INFO < (9, 0):
    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.

    from . import res_partner  # noqa
    from . import wizards  # noqa
    from . import contact_reference  # noqa
    from . import res_config  # noqa
