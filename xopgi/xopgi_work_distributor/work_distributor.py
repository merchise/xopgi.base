#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_work_distributor.work_distributor
# --------------------------------------------------------------------------
# Copyright (c) 2014 Merchise Autrement and Contributors
# All rights reserved.
#
# Author: Merchise Autrement
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.

from datetime import datetime, timedelta
from openerp import models, _, api, fields
from openerp.exceptions import ValidationError, Warning
from openerp.tools.safe_eval import safe_eval
from xoeuf.osv.orm import LINK_RELATED
from xoutil import logger


FIELD_NAME_TO_SHOW_ON_WIZARD = \
    lambda model: 'x_%s_ids' % model.replace('.', '_')

WIZARD_NAME = 'work.distributor.wizard'


def _evaluate_domain(dist_model, values):
    ''' Pop user lang information from context to allow put in domain names
    and search always on original text and not on user lang translations.

    '''
    group = False
    if dist_model.group_field:
        group = values.get(dist_model.group_field.name, False)
        if group:
            group = dist_model.env[dist_model.group_field.relation].browse(
                group)
    context = dict(dist_model.env.context)
    self = dist_model.env[dist_model.destination_field.relation]
    if not dist_model.domain or dist_model.domain.strip().startswith('['):
        domain = safe_eval(dist_model.domain or '[]')
    else:
        local_dict = locals()
        local_dict.update(globals().get('__builtins__', {}))
        safe_eval(dist_model.domain, local_dict, mode='exec', nocopy=True)
        domain = local_dict.get('result', [])
    context.pop('lang', False)
    return self.with_context(context).search(domain)


class WorkDistributionModel(models.Model):
    _name = 'work.distribution.model'

    def _get_models(self):
        return [
            (m.model, m.name)
            for m in self.env['ir.model'].search([('osv_memory', '=', False)])
        ]

    model = fields.Many2one(
        'ir.model', required=True,
        help='Model where Work Distribution Strategies will be applied.')
    group_field = fields.Many2one(
        'ir.model.fields', 'Group Field',
        help='many2one field where that it value determine domain of '
             'distribution destination.')
    strategy_by_group = fields.Boolean()
    domain = fields.Text(
        help='Odoo domain to search in destination_field`s model.',
        default='''
        #  Odoo domain like: [('field_name', 'operator', value)]
        #  or python code to return on result var a odoo domain like
        #  if uid != 1:
        #      result = [('id', '=', uid)]
        #  else:
        #      result = [('id', '!=', 1)]
        #  self, env, model, values, context and group are able to use:
        #  self => active model (on new api).
        #  dist_model => work distribution model config entry. (
        #      .destination_field (objective field)
        #      .group_field (field to get group)
        #      .strategy_by_group (if grouping or not)
        #  )
        #  values => python dict to passed to create method.
        #  context => active context.
        #  group => group object from value passed on create method.
        #  E.g: result = ([('id', 'in', group.members_field_name.ids)]
        #                 if group else [])
        ''')
    destination_field = fields.Many2one(
        'ir.model.fields', 'Destination Field', required=True,
        help='Field that it value it will determinate by distribution '
             'strategy apply.')
    other_fields = fields.Text(
        'Other fields', help='Python Dictionary with others variables (Keys) '
                             'used on some distribution strategy and '
                             'model\' fields where it value are. \n '
                             'Eg: {"date": "date_from"}', default='{}')
    strategy_ids = fields.Many2many(
        'work.distribution.strategy', 'distribution_model_strategy',
        'model_id', 'strategy_id', 'Strategies', required=True,
        help='Work Distribution Strategies possible to apply on this model '
             'objects.')
    action = fields.Many2one('ir.actions.act_window')
    strategy_field = fields.Many2one('ir.model.fields', 'Setting Field')

    @api.constrains('other_fields')
    def _check_other_fields(self):
        for model in self:
            fields_name = model.strategy_ids.get_fields_name()
            if fields_name:
                other_fields = safe_eval(model.other_fields or '{}')
                if not other_fields or not all(
                        other_fields.get(f, False) for f in fields_name):
                    raise ValidationError(
                        _('Other fields must define all fields used on '
                          'selected strategies.'))
                obj = self.pool.get(model.model.model)
                for field in other_fields.itervalues():
                    if not obj or not obj._fields.get(field, False):
                        raise ValidationError(
                            _('Some Other fields defined not exist on '
                              'destination model'))
        return True

    @api.constrains('strategy_ids')
    def _check_strategy_ids(self):
        for model in self:
            if not model.group_field and len(model.strategy_ids) > 1:
                raise ValidationError(
                    _('When no group field is defined only one strategy '
                      'must be selected.'))
        return True

    @api.model
    @api.onchange('strategy_ids')
    def onchange_strategy_ids(self):
        warning = False
        try:
            other_fields = safe_eval(self.other_fields or '{}')
        except (ValueError, SyntaxError, ):
            other_fields = {}
            warning = {
                'title': _('Warning!'),
                'message': _('Other fields must be a python dict.')
            }
        fields_name = self.strategy_ids.get_fields_name()
        other_fields.update({n: n
                             for n in fields_name - set(other_fields)})
        self.other_fields = str(other_fields)
        return {'warning': warning} if warning else None

    @api.model
    def distribute(self, model, values):
        ''' Get all distribution configurations for model and apply each one.

        '''
        for item in self.search([('model.model', '=', model)]):
            strategy = False
            if item.group_field:
                group_id = values.get(item.group_field.name, False)
                if group_id:
                    group_model = item.group_field.relation
                    group = self.env[group_model].browse(group_id)
                    strategy = getattr(group, item.strategy_field.name, False)
            else:
                strategy = item.strategy_ids[0]
            if strategy:
                other_fields = (safe_eval(item.other_fields)
                                if item.other_fields else {})
                # TODO: check if active user have access to destination field
                val = strategy.apply(item, values, **dict(other_fields))
                if val is not None:
                    values[item.destination_field.name] = val
        return values

    @api.model
    def unlink_rest(self):
        self.search([('id', 'not in', self.ids)]).unlink()

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, values):
        if values.get('group_field', False):
            self.sudo().create_related(values)
        res_id = super(WorkDistributionModel, self).create(values)
        return res_id

    def create_related(self, values):
        """ Create action and field associated.

        """
        field_obj = self.env['ir.model.fields']
        destination_field = field_obj.browse(values['destination_field'])
        group_field = field_obj.browse(values['group_field'])
        model_id = values.get('model', False)
        model = self.env['ir.model'].browse(model_id)
        strategy_field = self.create_field(group_field.relation, model.model,
                                           destination_field.name)
        action = self.create_actions(
            group_field.relation, model.name,
            destination_field.field_description, strategy_field)
        values.update(dict(strategy_field=strategy_field, action=action))

    def create_field(self, group_model, model, destination_field_name):
        ''' Create field to save which distribution strategy use on each
        group_field model objects.

        '''
        field_obj = self.env['ir.model.fields']
        model_obj = self.env['ir.model']
        group_model = model_obj.search([('model', '=', group_model)])
        field_base_name = '%s_%s' % (model.replace('.', '_'),
                                     destination_field_name)
        field_name = 'x_%s_ids' % field_base_name
        field_data = {
            'model': group_model[0].model,
            'model_id': group_model.ids[0],
            'name': field_name,
            'relation': 'work.distribution.strategy',
            'field_description':
                "Set %s Work Distribution Strategy" % field_base_name,
            'state': 'manual',
            'ttype': 'many2one'
        }
        new_field = field_obj.create(field_data)
        self.create_ir_model_data_reference('ir.model.fields',
                                            new_field.id, field_name)
        return new_field.id

    def create_actions(self, group_model, model_name, destination_field,
                       strategy_field_id):
        ''' Create actions to config with strategy use on each group_field
        model objects.

        '''
        action_obj = self.env['ir.actions.act_window']
        value_obj = self.env['ir.values']
        name = ("Define work Distribution Strategy for '%s' on '%s'"
                % (destination_field, model_name))
        rol = self.env.ref('xopgi_work_distributor.group_distributor_manager',
                           raise_if_not_found=False)
        new_act = action_obj.create({
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': WIZARD_NAME,
            'src_model': group_model,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'groups_id': LINK_RELATED(rol.id) if rol else False,
            'context': {
                'strategy_field_id': strategy_field_id,
                'field_to_show': FIELD_NAME_TO_SHOW_ON_WIZARD(group_model)
            }
        })
        self.create_ir_model_data_reference('ir.actions.act_window',
                                            new_act.id, name)
        new_val = value_obj.create({
            'name': name,
            'model': group_model,
            'key2': 'client_action_multi',
            'value': "ir.actions.act_window," + str(new_act.id)
        })
        self.create_ir_model_data_reference('ir.values',
                                            new_val.id, name)
        return new_act.id

    def create_ir_model_data_reference(self, model, res_id, name):
        '''Create ir.model.data entry for each field, action or value
        created on run time, to ensure it be removed at module
        uninstall.
        '''
        self.env['ir.model.data'].create({
            'model': model,
            'res_id': res_id,
            'module': 'xopgi_work_distributor',
            'name': '%s-%s' % (model, name),
            'noupdate': True
        })

    def unlink(self):
        """ Unlink action and field associated.

        """
        actions_to_unlink = [i.action.id for i in self if i.action]
        fields_to_unlink = [i.strategy_field.id for i in self
                            if i.strategy_field]
        result = super(WorkDistributionModel, self).unlink()
        self.sudo().unlink_actions(actions_to_unlink)
        self.sudo().unlink_fields(fields_to_unlink)
        return result

    def unlink_actions(self, actions_to_unlink):
        '''Remove actions of distributions model unlinked.

        '''
        if not actions_to_unlink:
            return
        model = 'ir.actions.act_window'
        self.unlink_ir_model_data_reference(model, actions_to_unlink)
        self.env[model].browse(actions_to_unlink).unlink()
        for action_id in actions_to_unlink:
            args = [('value', '=', "%s,%d" % (model, action_id))]
            values = self.env['ir.values'].search(args)
            if values:
                self.unlink_ir_model_data_reference('ir.values', values.ids)
                values.unlink()

    def unlink_fields(self, fields_to_unlink):
        '''Remove fields of distributions model unlinked.

        '''
        if not fields_to_unlink:
            return
        model = 'ir.model.fields'
        self.unlink_ir_model_data_reference(model, fields_to_unlink)
        self.env[model].browse(fields_to_unlink).unlink()

    def unlink_ir_model_data_reference(self, model, ids):
        self.env['ir.model.data'].search([
            ('model', '=', model),
            ('res_id', 'in', ids),
            ('module', '=', 'xopgi_work_distributor')
        ]).unlink()

    @api.multi
    def write(self, values):
        if 'group_field' in values or 'destination_field' in values:
            actions_to_unlink = [i.action.id for i in self if i.action]
            fields_to_unlink = [i.strategy_field.id for i in self
                                if i.strategy_field]
            self.sudo().unlink_actions(actions_to_unlink)
            self.sudo().unlink_fields(fields_to_unlink)
        result = super(WorkDistributionModel, self).write(values)
        if values.get('group_field', False):
            for item in self:
                vals = {'destination_field': item.destination_field.id,
                        'group_field': item.group_field.id}
                self.create_related(vals)
                vals.pop('destination_field', False)
                vals.pop('group_field', False)
                item.write(vals)
        return result


class WorkDistributionStrategy(models.Model):
    _name = 'work.distribution.strategy'

    name = fields.Char(required=True, translate=True)
    predefine = fields.Boolean()
    code = fields.Text(required=True, default='''
        #  Python code to return on result var value to set on
        #  destination field or None to no update it.
        #  E.g: result = False
        #  self, dist_model, values, candidates and **kwargs are able to use:
        #  self => active strategy (on new api).
        #  dist_model => active model name.
        #  values => python dict to passed to create method.
        #  **kwargs => python dict set on field ``other fields``.
        ''')
    other_fields = fields.Char(
        help='Python List with others variables'
             'needed on this distribution strategy.\n '
             'Eg: ["date", "qtty"]', default='[]')

    _sql_constraints = [
        ('name_unique', 'unique (name)', 'Strategy must be unique!')
    ]

    def apply(self, dist_model, values, **kwargs):
        method = (getattr(self, self.code, None)
                  if self.predefine else self.custom)
        candidates = _evaluate_domain(dist_model, values)
        if method and candidates:
            try:
                return method(dist_model, candidates, values, **kwargs)
            except:
                logger.exception(
                    'An error happen trying to execute work distribution for '
                    'Model: %s, Field: %s,' %
                    (dist_model.destination_field.model,
                     dist_model.destination_field.name))
        return None

    def uniform(self, dist_model, candidates, values, **kwargs):
        """Detect the next corresponding domain id and update values with it.

        """
        table = self.pool[dist_model.model.model]._table
        if dist_model.group_field:
            query = ("SELECT %s FROM %s WHERE %s = %%s ORDER BY id DESC" %
                     (dist_model.destination_field.name, table,
                      dist_model.group_field.name))
            params = (values.get(dist_model.group_field.name, False),)
        else:
            query = ("SELECT %s FROM %s WHERE %s in %%s ORDER BY id DESC" %
                     (dist_model.destination_field.name, table,
                      dist_model.destination_field.name))
            params = (tuple(candidates.ids),)
        self.env.cr.execute(query, params=params)
        last_dist = self.env.cr.fetchone()
        last_dist = last_dist[0] if last_dist and last_dist[0] else 0
        next_dist = (
            min(_id for _id in candidates.ids if _id > last_dist)
            if last_dist and any(_id > last_dist
                                 for _id in candidates.ids)
            else candidates.ids[0]
        )
        return next_dist

    def effort(self, dist_model, candidates, values, **kwargs):
        return self._effort(dist_model, candidates, values)

    def effort_month(self, dist_model, candidates, values, **kwargs):
        model = self.env[dist_model.model.model]
        DAYS = 30
        low_date = datetime.now()
        upp_date = low_date + timedelta(DAYS)
        date_field = model._fields[kwargs.get('date_start')]
        format = (fields.DATETIME_FORMAT
                  if isinstance(date_field, fields.Datetime)
                  else fields.DATE_FORMAT)
        strlow_date = low_date.strftime(format)
        strupp_date = upp_date.strftime(format)
        return self._effort(
            dist_model, candidates, values, date_field=date_field.name,
            date_start=strlow_date, date_end=strupp_date)

    def _effort(self, dist_model, candidates, values, date_field=False,
                date_start=False, date_end=False):
        model = self.env[dist_model.model.model]
        min_value = None
        next_dist = False
        group_field_name = (dist_model.group_field.name
                            if dist_model.group_field else False)
        args = ([(group_field_name, '=', values[group_field_name])]
                if group_field_name else [])
        if date_field:
            args.extend([(date_field, '>=', date_start),
                         (date_field, '<=', date_end)])
        for x in candidates.ids:
            current_effort = model.search_count(
                args + [(dist_model.destination_field.name, '=', x)])
            if min_value is None or min_value > current_effort:
                min_value = current_effort
                next_dist = x
        return next_dist

    def custom(self, dist_model, candidates, values, **kwargs):
        if self.code.strip().startswith('{'):
            return safe_eval(self.code or '{')
        else:
            local_dict = locals()
            local_dict.update(globals().get('__builtins__', {}))
            safe_eval(self.code, local_dict, mode='exec', nocopy=True)
            return local_dict.get('result', None)

    @api.model
    def get_fields_name(self, mixed=True):
        result = []
        method = getattr(result, 'extend' if mixed else 'append')
        for strategy in self:
            method(safe_eval(strategy.other_fields)
                   if strategy.other_fields else [])
        return set(result) if mixed else result


class WorkDistributorWizard(models.TransientModel):
    _name = WIZARD_NAME

    name = fields.Char()
    strategy_id = fields.Many2one(
        'work.distribution.strategy', 'Strategy',
        help='Strategy of work distribution to apply to this items.')
    info = fields.Text()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        result = super(WorkDistributorWizard, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type != 'form' or not result.get('fields', {}).get(
                'strategy_id', False):
            return result
        active_model = self.env.context.get('active_model', False)
        model = self.env['work.distribution.model'].search(
            [('group_field.relation', '=', active_model)])
        result['fields']['strategy_id']['domain'] = [
            ('id', 'in', model.strategy_ids.ids)]
        return result

    @api.model
    def default_get(self, fields_list):
        values = super(WorkDistributorWizard, self).default_get(fields_list)
        if 'info' in fields_list:
            active_ids = self.env.context.get('active_ids', False)
            active_model = self.env.context.get('active_model', False)
            ir_model = self.env['ir.model']
            model = ir_model.search([('model', '=', active_model)])[0]
            field = self.env['ir.model.fields'].browse(
                self.env.context.get('strategy_field_id'))
            names = [_('%s\n       Strategy: %s') %
                     (item.name_get()[0][1],
                      getattr(item, field.name).name or '')
                     for item in self.env[active_model].browse(active_ids)]
            info = _("%s(s) to set work distribution strategy:\n"
                     "     * %s") % (model.name, '\n     * '.join(names))
            values.update({'info': info})
        return values

    @api.guess
    def action_config(self, *args, **Kargs):
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        res = super(WorkDistributorWizard, self).create(vals)
        active_ids = self.env.context.get('active_ids', False)
        active_model = self.env.context.get('active_model', False)
        field = self.env['ir.model.fields'].browse(
            self.env.context.get('strategy_field_id'))
        if not active_model:
            raise Warning(_('Configuration Error!'),
                          _('The is no active model defined!'))
        self.env[active_model].browse(active_ids).write(
            {field.name: res.strategy_id.id})
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
