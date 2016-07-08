# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_web_notification.notification
# ---------------------------------------------------------------------
# Copyright (c) 2016 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-04-19

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from openerp import models
from openerp.addons.bus import bus
from openerp.http import request

CHANNELS = {'notify': 'res_user_notify', 'warn': 'res_user_warn'}


class Controller(bus.Controller):
    def _poll(self, dbname, channels, last, options):
        if request.session.uid:
            channels = channels + [(request.db, channel, request.uid)
                                   for channel in CHANNELS.values()]
        return super(Controller, self)._poll(dbname, channels, last, options)


class XopgiWebNotification(models.TransientModel):
    _name = 'xopgi.web.notification'

    def notify(self, uid=None, **values):
        return self.post(uid or self._uid, **values)

    def warn(self, uid=None, **values):
        return self.post(uid or self._uid, 'warn', **values)

    def post(self, uid, action='notify', channel=None, **values):
        if not channel:
            channel = (self._cr.dbname, CHANNELS[action], uid)
        return self._post(channel, **values)

    def _post(self, channel, **values):
        return self.env['bus.bus'].sendone(channel, values)
