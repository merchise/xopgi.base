#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# res_partner
# ---------------------------------------------------------------------
# Copyright (c) 2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2017-01-26


from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoeuf import api, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.multi
    def _track_subtype(self, init_values):
        '''Give the subtypes triggered by the changes on the record according
        to values that have been updated:(partner_id, acc_number, bank_name)

        :param init_values: the original values of the record; only modified fields
                            are present in the dict
        :returns: a subtype xml_id or False if no subtype is trigerred
        '''
        self.ensure_one()
        if 'partner_id' in init_values:
            return 'xopgi_track_partner.mt_bank_partner_id'
        elif 'acc_number' in init_values and self.create_date != self.write_date:
            return 'xopgi_track_partner.mt_bank_acc_number'
        elif 'bank_name' in init_values and self.create_date != self.write_date:
            return 'xopgi_track_partner.mt_bank_name'
        return super(ResPartnerBank, self)._track_subtype(init_values)
