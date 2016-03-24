# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_cdr_notification.controllers.main
# ---------------------------------------------------------------------
# Copyright (c) 2016 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2016-03-24

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from openerp import http as http
from openerp.http import request


class cdr_event_notification(http.Controller):

    # Function used, in RPC to check every 5 minutes, if notification to do for an event or not
    @http.route('/xopgi_cdr_notification/notify', type='json', auth="none")
    def notify(self):
        registry = request.registry
        uid = request.session.uid
        context = request.session.context
        with registry.cursor() as cr:
            res = registry.get("cdr.js.notification").get_notifications(
                cr, uid, context=context)
            return res
