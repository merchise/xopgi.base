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

from xoeuf.odoo import models
from xoeuf.odoo import _


class objectmerge_mail(models.TransientModel):
    _inherit = 'object.merger'

    def _check_on_alias_defaults(self, sources, target):
        """Check if any of merged sources are referenced on any mail.alias
        and on this case update the references to the target.
        """
        query = """SELECT id, alias_defaults FROM mail_alias
                         WHERE alias_model_id = {model_id}
                         AND (alias_defaults LIKE '%''{field}''%')"""
        model = sources._name
        self._cr.execute("SELECT name, model_id, ttype FROM ir_model_fields "
                         "WHERE relation='%s';" % model)
        read = self._cr.fetchall()
        for field, model_id, ttype in read:
            self._cr.execute(query.format(model_id=model_id, field=field))
            for alias_id, defaults in self._cr.fetchall():
                mail_alias = self.env['mail.alias'].browse(alias_id)
                try:
                    defaults_dict = dict(eval(defaults))
                except Exception:
                    defaults_dict = {}
                val = defaults_dict.get(field, False)
                if not val:
                    continue
                if ttype == 'many2one':
                    if val in sources.ids and val != target.id:
                        defaults_dict[field] = target.id
                        mail_alias.sudo().write(
                            {'alias_defaults': repr(defaults_dict)}
                        )
                else:
                    res_val = []
                    for rel_item in val:
                        rel_ids = rel_item[-1]
                        if isinstance(rel_ids, (tuple, list)):
                            wo_partner_ids = [i for i in rel_ids if i not in sources.ids]
                            if wo_partner_ids != rel_ids:
                                rel_ids = set(wo_partner_ids + [target.id])
                        elif rel_ids in sources.ids and val != target.id:
                            rel_ids = target.id
                            res_val.append(tuple(rel_item[:-1]) + (rel_ids,))
                    if val != res_val:
                        defaults_dict[field] = res_val
                        mail_alias.sudo().write(
                            {'alias_defaults': repr(defaults_dict)}
                        )
        return True

    def _notify_merge(self, sources, target):
        try:
            src_names = sources.name_get()
            if src_names:
                subject = _('%s(s) Merged') % target._description
                body = '<br/>'.join([_('<b>ID:</b> %s; <b>Name:</b> %s') % id_name
                                     for id_name in src_names])
                return target.message_post(body=body, subject=subject)
        except Exception:
            return None

    def merge(self, sources, target):
        res = super(objectmerge_mail, self).merge(
            sources,
            target
        )
        sources -= target
        self._check_on_alias_defaults(sources, target)
        self._notify_merge(sources, target)
        return res
