# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board
# ---------------------------------------------------------------------
# Copyright (c) 2013-2016 Merchise Autrement
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-10-29

from __future__ import absolute_import as _py3_abs_imports

from openerp.release import version_info as ODOO_VERSION_INFO

if ODOO_VERSION_INFO < (9, 0):
    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.

    from . import board  # noqa
    from . import board_widget  # noqa
    from . import hr_job  # noqa
    from . import res_config  # noqa
    from . import res_currency  # noqa
