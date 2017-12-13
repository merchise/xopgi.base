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
from xoeuf.odoo import SUPERUSER_ID


def migrate(what, *args):
    # XXX: Odoo 10+ passes env directly
    if isinstance(what, api.Environment):
        env = what
        cr = what.cr
    else:
        cr = what
        env = api.Environment(cr, SUPERUSER_ID, {})

    # Since recurrence_def_pre_migration is not a field we must SQL
    cr.execute('SELECT id, recurrence_def_pre_migration FROM cdr_recurrent_event'
               '  WHERE recurrence_def_pre_migration IS NOT NULL')

    RecurrentModel = env['recurrent.model']
    CDRRecurrentEvent = env['cdr.recurrent.event']
    CDRRecurrentEventDefinition = env['cdr.recurrent.event.def']
    events_map = {
        CDRRecurrentEvent.browse(id): RecurrentModel.browse(evid)
        for id, evid in cr.fetchall()
    }
    for cdr_event, recurrence in events_map.items():
        vals = recurrence.read(CDRRecurrentEventDefinition._fields)
        vals.pop('id')
        cdr_event.recurrence_def = CDRRecurrentEventDefinition.create(vals)
