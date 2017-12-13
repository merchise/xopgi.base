#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

'''Convert our System Event to a 'Recurrent Model'.

'''

from xoeuf import api


def migrate(what, *args):
    # XXX: Odoo 10+ passes env directly
    if isinstance(what, api.Environment):
        cr = what.cr
    else:
        cr = what
    # At this point Odoo has not created the 'cdr.recurrent.event.def' table.
    # However, we can convert the 'recurrence' field in 'cdr.system.event' to
    # the a new 'recurrent_def_pre_migration_copy' column.  At post-migration
    # we then can simply copy the data from 'recurrent.model' to
    # 'cdr.recurrent.event.def'.
    cr.execute(
        'ALTER TABLE cdr_recurrent_event '
        'ADD COLUMN recurrence_def_pre_migration INTEGER'
    )
    cr.execute(
        'UPDATE cdr_recurrent_event '
        'SET recurrence_def_pre_migration=recurrence'
    )
