#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_work_distributor.migrations.1.2.post-001-load-translations
# ---------------------------------------------------------------------
# Copyright (c) 2015, 2016 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-07-010

'''Get missing translations.

'''

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from openerp import SUPERUSER_ID
from xoutil.modules import modulemethod


@modulemethod
def migrate(self, cr, version):
    from openerp.modules.registry import RegistryManager as manager
    self = manager.get(cr.dbname)['work.distribution.model']
    distribution_ids = self.search(cr, SUPERUSER_ID,
                                   [('translations', '=', False)])
    self.update_translations(cr, SUPERUSER_ID, distribution_ids)
