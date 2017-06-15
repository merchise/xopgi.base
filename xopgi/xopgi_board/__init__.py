# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board
# ---------------------------------------------------------------------
# Copyright (c) 2013-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2015-10-29

from __future__ import absolute_import as _py3_abs_imports

try:
    from openerp.release import version_info as ODOO_VERSION_INFO
except ImportError:
    # This is Odoo 10+, but let's be able to get the ODOO_VERSION_INFO
    from odoo.release import version_info as ODOO_VERSION_INFO


if ODOO_VERSION_INFO < (9, 0):
    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.

    from . import board  # noqa
    from . import board_widget  # noqa
    from . import hr_job  # noqa
    from . import res_config  # noqa
    from . import res_currency  # noqa
    from . import res_group  # noqa
    from . import ir_ui_menu  # noqa


def get_var_value(self, xml_id, module):
    '''Get the value of variable defined with an XML id.

    '''
    module = module.rsplit('.', 1)[-1]  # Allow module to be fully qualified
                                        # so you can say __name__  # noqa
    var = self.env.ref('%s.%s' % (module, xml_id), raise_if_not_found=False)
    return var._value() if var else None
