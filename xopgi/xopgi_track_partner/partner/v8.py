#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# v8
# ---------------------------------------------------------------------
# Copyright (c) 2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2017-09-29

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoeuf import models


class PartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    _track = {
        'partner_id': {
            'xopgi_track_partner.mt_bank_partner_id':
                lambda self, cr, uid, obj, ctx=None: obj.partner_id and obj.partner_id.id
        },
        'acc_number': {
            'xopgi_track_partner.mt_bank_acc_number':
                lambda self, cr, uid, obj, ctx=None: obj.acc_number and obj.create_date != obj.write_date
        },
        'bank_name': {
            'xopgi_track_partner.mt_bank_name':
                lambda self, cr, uid, obj, ctx=None: obj.bank_name and obj.create_date != obj.write_date
        }
    }
