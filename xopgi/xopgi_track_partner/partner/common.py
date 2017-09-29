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

import logging
_logger = logging.getLogger(__name__)
del logging


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _setup_complete(self):
        # Instead of rewriting the columns, we simply add the required
        # attribute to the fields after the model is properly setup.
        # TODO: This is kind of a hack... but rewriting the entire column just
        # to add a metadata-like attribute seems overreaching.
        super(ResPartner, self)._setup_complete()
        for field in ('active', 'name', 'function', 'phone', 'mobile', 'email',
                      'customer', 'supplier', 'contact_address', 'street',
                      'street2', 'city', 'state_id', 'zip', 'country_id'):
            _logger.debug('Tracking field %r', field)
            self._fields[field].track_visibility = 'onchange'


class ResPartnerBank(models.Model):
    '''This is the association of the partner with his bank accounts.

    It is important that when the partner bank changes, a notification occurs
    to those followers of the partner.
    '''
    _inherit = ['res.partner.bank', 'mail.thread']
    _name = 'res.partner.bank'

    @api.model
    def _setup_complete(self):
        # Instead of rewriting the columns, we simply add the required
        # attribute to the fields after the model is properly setup.
        # TODO: This is kind of a hack... but rewriting the entire column just
        # to add a metadata-like attribute seems overreaching.
        super(ResPartnerBank, self)._setup_complete()
        for field in ('acc_number', 'partner_id', 'bank_name'):
            _logger.debug('Tracking field %r', field)
            self._fields[field].track_visibility = 'onchange'
