#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoeuf import MAJOR_ODOO_VERSION

if MAJOR_ODOO_VERSION in (10, ):
    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.

    from . import board  # noqa
    from . import board_widget  # noqa
    from . import hr_job  # noqa
    from . import res_config  # noqa
    from . import res_currency  # noqa
    from . import res_group  # noqa
    from . import ir_ui_menu  # noqa

    from .res_config import BoardValue  # noqa: public API


def get_var_value(self, xml_id, module):
    '''Get the value of variable defined with an XML id.

    '''
    module = module.rsplit('.', 1)[-1]  # Allow module to be fully qualified
                                        # so you can say __name__  # noqa
    var = self.env.ref('%s.%s' % (module, xml_id), raise_if_not_found=False)
    return var.result if var else None
