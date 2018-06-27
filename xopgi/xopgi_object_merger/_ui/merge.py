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


from lxml import etree
from lxml.builder import E
from odoo.osv.orm import setup_modifiers
from xoeuf import api, models
from odoo import _
from xoeuf.models.extensions import get_treeview_action


class ir_model(models.Model):
    _inherit = 'ir.model'

    @api.multi
    def action_merge_view(self):
        '''Merger objects from models that do not have a menu entry,
        Models that do not have the reserved field name are built
        in a view by removing the automatic fields.

        '''
        active_model = self.model
        description = self.env[active_model]._description
        field_names = self._get_show_fields(active_model)
        if 'name' in field_names:
            res = get_treeview_action(self.env[active_model])
            res['name'] = 'Merge %s' % description
            res['context'] = {'create': False}
        else:
            res = self._get_model_merger_view(field_names, active_model)
        return res

    def _get_show_fields(self, active_model):
        fields_name = [name for name, field in self.env[active_model]._fields.items() if not field.automatic]
        # Show the `id` field in the view of the merge wizard
        fields_name.insert(0, 'id')
        return fields_name

    def _get_model_merger_view(self, field_names, active_model):
        tree = self.env.ref('xopgi_object_merger.view_merger_tree')
        tree.model = active_model
        self._get_view_field_tree(tree, field_names)
        res = get_treeview_action(self.env[active_model])
        res['name'] = _("Merger object")
        res['view_id'] = tree.id
        res['context'] = {'force_view': True, 'create': False}
        return res

    def _get_view_field_tree(self, tree, field_names):
        '''Build the tree view

        '''
        node_list = []
        tree.arch = '<tree></tree>'
        doc = etree.XML(tree.arch)
        tree_add = doc.xpath("//tree")
        if field_names:
            fields_to_add = self.env[self.model].fields_get(field_names)
        field_list = self._build_fields_nodes(field_names, fields_to_add, node_list)
        [tree_add[0].append(field) for field in field_list]
        tree.arch = etree.tostring(doc)

    def _build_fields_nodes(self, field_names, fields_to_add, node_list):
        for field in field_names:
            node_list.extend(
                self._build_field_node(field, fields_to_add)
            )
        return node_list

    def _build_field_node(self, field, fields_to_add):
        node = E.field(dict(name=field))
        setup_modifiers(node, fields_to_add[field])
        return [node]
