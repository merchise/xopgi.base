#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# --------------------------------------------------------------------------
# xopgi_work_distributor.work_distributor
# --------------------------------------------------------------------------
# Copyright (c) 2014-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# Author: Merchise Autrement [~º/~]
# Contributors: see CONTRIBUTORS and HISTORY file
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from datetime import timedelta
from xoutil import logger

from openerp import models, _, api, fields
from openerp.exceptions import ValidationError, Warning
from openerp.tools.safe_eval import safe_eval

from xoeuf import signals
from xoeuf.osv.orm import LINK_RELATED, REPLACEWITH_RELATED
from xoeuf.tools import date2str, dt2str, normalize_datetime


FIELD_NAME_TO_SHOW_ON_WIZARD = \
    lambda model: 'x_%s_ids' % model.replace('.', '_')

WIZARD_NAME = 'work.distributor.wizard'

DOMAIN_DEFAULT = '''
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
'''


def _evaluate_domain(dist_model, values):
    ''' Pop user lang information from context to allow put in domain names
    and search always on original text and not on user lang translations.

    '''
    domain = dist_model.domain or dist_model.build_domain
    self = dist_model.env[dist_model.destination_field.relation]
    context = dict(dist_model.env.context, lang=False)
    if not domain or all(l.strip().startswith('#')
                         for l in domain.splitlines()
                         if l.strip()):
        domain = []
    else:
        group = False
        if dist_model.group_field:
            group = values.get(dist_model.group_field.name, False)
            if group:
                group = self.browse(group)
        if any(l.strip().startswith('result')
               for l in domain.splitlines()):
            local_dict = locals()
            local_dict.update(globals().get('__builtins__', {}))
            safe_eval(domain, local_dict, mode='exec', nocopy=True)
            domain = local_dict.get('result', [])
        else:
            domain = safe_eval(domain)
    return self.with_context(context).search(domain)


WORKDIST_MODELNAME = 'work.distribution.model'


class WorkDistributionModel(models.Model):
    _name = WORKDIST_MODELNAME

    def _get_models(self):
        return [
            (m.model, m.name)
            for m in self.env['ir.model'].search([('osv_memory', '=', False)])
        ]

    model = fields.Many2one(
        'ir.model', required=True,
        help='Model where Work Distribution Strategies will be applied.')
    model_name = fields.Char(related='model.model', readonly=True)
    group_field = fields.Many2one(
        'ir.model.fields', 'Group Field',
        help='many2one field where that it value determine domain of '
             'distribution destination.')
    strategy_by_group = fields.Boolean()
    use_domain_builder = fields.Boolean()
    domain = fields.Text(
        help='Odoo domain to search in destination_field`s model.',
        default=lambda self: _(DOMAIN_DEFAULT))
    build_domain = fields.Char(
        help='Odoo domain to search in destination_field`s model.',
        string='Domain')
    destination_field = fields.Many2one(
        'ir.model.fields', 'Destination Field', required=True,
        help='Field that it value it will determinate by distribution '
             'strategy apply.')
    destination_model = fields.Char(related='destination_field.relation',
                                    readonly=True)
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
    when_apply = fields.Selection(
        [('all', 'Always'), ('no_set', 'When no value set')], default='all')
    effort_domain = fields.Text(help="Odoo domain to use on effort "
                                     "based strategies. \nEg: "
                                     "[('state','not in',('done','cancel')]")
    translations = fields.Many2many('ir.translation')

    @api.onchange('use_domain_builder')
    def onchange_use_domain_builder(self):
        if self.use_domain_builder:
            self.build_domain = ''
            self.domain = ''
        else:
            self.domain = (self.build_domain or '') + _(DOMAIN_DEFAULT)

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
    @api.onchange('strategy_by_group')
    def onchange_strategy_by_group(self):
        if not self.strategy_by_group:
            self.group_field = False

    @signals.receiver(signals.pre_create)
    def distribute(self, signal, values):
        ''' Get all distribution configurations for model and apply each one.

        '''
        dist_model = self.env[WORKDIST_MODELNAME]
        for item in dist_model.search([('model.model', '=', self._name)]):
            if item.applicable(values):
                strategy = False
                if item.group_field:
                    group_id = values.get(item.group_field.name, False)
                    if group_id:
                        group_model = item.group_field.relation
                        group = self.env[group_model].browse(group_id)
                        strategy = getattr(group, item.strategy_field.name,
                                           False)
                else:
                    strategy = item.strategy_ids[0]
                if strategy:
                    other_fields = (safe_eval(item.other_fields)
                                    if item.other_fields else {})
                    # TODO: check if active user have access to destination
                    # field
                    val = strategy.apply(item, values, **dict(other_fields))
                    if val is not None:
                        values[item.destination_field.name] = val
        return values

    def applicable(self, values):
        if not self.when_apply or self.when_apply == 'all':
            return True
        else:
            return not values.get(self.destination_field.name, False)

    @api.model
    def unlink_rest(self):
        self.search([('id', 'not in', self.ids)]).unlink()

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, values):
        if values.get('group_field', False):
            self.sudo().create_related(values)
        res = super(WorkDistributionModel, self).create(values)
        res.update_translations()
        return res

    def create_related(self, values):
        """ Create action and field associated.

        """
        field_obj = self.env['ir.model.fields']
        destination_field = field_obj.browse(values['destination_field'])
        group_field = field_obj.browse(values['group_field'])
        model_id = values.get('model', False)
        model = self.env['ir.model'].browse(model_id)
        strategy_field = self.create_field(group_field.relation, model,
                                           destination_field)
        action = self.create_actions(
            group_field.relation, model.name,
            destination_field.field_description, strategy_field)
        values.update(dict(strategy_field=strategy_field, action=action))

    def create_field(self, group_model, model, destination_field):
        ''' Create field to save which distribution strategy use on each
        group_field model objects.

        '''
        field_obj = self.env['ir.model.fields']
        model_obj = self.env['ir.model']
        group_model = model_obj.search([('model', '=', group_model)])
        field_base_name = '%s_%s' % (model.model.replace('.', '_'),
                                     destination_field.name)
        field_name = 'x_%s_id' % field_base_name
        field_data = {
            'model': group_model[0].model,
            'model_id': group_model.ids[0],
            'name': field_name,
            'relation': 'work.distribution.strategy',
            'field_description':
                _("Work Distribution Strategy for %s on %s") %
                (destination_field.field_description, model.name),
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
        name = (_("Define Work Distribution Strategy for '%s' on '%s'")
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
        self.update_translations(force_delete=True)
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
        temp_fields = ['destination_field', 'group_field', 'model']
        if any(f in values for f in temp_fields):
            actions_to_unlink = [i.action.id for i in self if i.action]
            fields_to_unlink = [i.strategy_field.id for i in self
                                if i.strategy_field]
            self.sudo().unlink_actions(actions_to_unlink)
            self.sudo().unlink_fields(fields_to_unlink)
            for item in self.sudo():
                if item.translations:
                    item.translations.unlink()
        result = super(WorkDistributionModel, self).write(values)
        group_field = values.get('group_field', False)
        if any(values.get(f, False) for f in temp_fields):
            for item in self:
                temp_fields = ['destination_field', 'group_field', 'model']
                vals = {f: getattr(item, f).id for f in temp_fields}
                self.create_related(vals)
                for f in temp_fields:
                    vals.pop(f, None)
                item.write(vals)
        if any(f in values for f in temp_fields):
            self.update_translations(force_create=group_field)
        return result

    @api.multi
    def update_translations(self, force_create=False, force_delete=False):
        to_unlink = self.env['ir.translation']
        for item in self:
            if not force_delete and item.group_field:
                if force_create or not item.translations:
                    translations = self.create_translations(
                        item.group_field.relation, item.strategy_field.name,
                        item.strategy_field.field_description,
                        type='field')
                    translations |= self.create_translations(
                        'ir.actions.act_window', 'name', item.action.name,
                        res_id=item.action.id)
                    item.write(dict(
                        translations=[REPLACEWITH_RELATED(*translations.ids)]
                    ))
            if item.translations and (force_delete or not item.group_field):
                to_unlink |= item.translations
        if to_unlink:
            to_unlink.unlink()

    def create_translations(self, model, field, src, res_id=0, type='model'):
        result = self.env['ir.translation']
        for lang in self.env['res.lang'].search([]):
            result |= result.create({
                'type': type,
                'res_id': res_id,
                'module': 'xopgi_work_distributor',
                'name': '%s,%s' % (model, field),
                'src': src,
                'value': src,
                'lang': lang.code
            })
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
        candidates = candidates.sorted(key=lambda r: r.id)
        return next(
            (id for id in candidates.ids if not last_dist or id > last_dist),
            candidates.ids[0]
        )

    def effort(self, dist_model, candidates, values, **kwargs):
        return self._effort(dist_model, candidates, values)

    def _effort_commons(self, dist_model, **kwargs):
        model = self.env[dist_model.model.model]
        today = normalize_datetime(fields.Date.context_today(self))
        date_field = model._fields[kwargs.get('date_start')]
        to_str = date2str if isinstance(date_field, fields.Date) else dt2str
        return model, today, date_field, to_str

    def effort_month(self, dist_model, candidates, values, **kwargs):
        model, low_date, date_field, to_str = self._effort_commons(dist_model,
                                                                   **kwargs)
        DAYS = 30
        upp_date = low_date + timedelta(DAYS)
        strlow_date = to_str(low_date)
        strupp_date = to_str(upp_date)
        return self._effort(
            dist_model, candidates, values, date_field=date_field.name,
            date_start=strlow_date, date_end=strupp_date)

    def around_effort(self, dist_model, candidates, values, **kwargs):
        model, today, date_field, to_str = self._effort_commons(dist_model,
                                                                **kwargs)
        DAYS = 7
        TOTAL_DAYS = DAYS * 2 + 1
        item_date = values.get(kwargs.get('date_start'), False)
        item_date = normalize_datetime(item_date) if item_date else today
        low_date = (today
                    if item_date < today + timedelta(DAYS)
                    else item_date - timedelta(DAYS))
        upp_date = low_date + timedelta(TOTAL_DAYS)
        strlow_date = to_str(low_date)
        strupp_date = to_str(upp_date)
        return self._effort(
            dist_model, candidates, values,
            date_field=date_field.name, date_start=strlow_date,
            date_end=strupp_date
        )

    def future_effort(self, dist_model, candidates, values, **kwargs):
        model, today, date_field, to_str = self._effort_commons(dist_model,
                                                                **kwargs)
        return self._effort(
            dist_model, candidates, values,
            date_field=date_field.name, date_start=to_str(today)
        )

    def _effort(self, dist_model, candidates, values, date_field=False,
                date_start=False, date_end=False):
        model = self.env[dist_model.model.model]
        min_value = None
        next_dist = False
        group_field_name = (dist_model.group_field.name
                            if dist_model.group_field else False)
        args = ([(group_field_name, '=', values[group_field_name])]
                if group_field_name else [])
        args.extend(safe_eval(dist_model.effort_domain)
                    if dist_model.effort_domain else [])
        if date_field:
            if date_start:
                args.append((date_field, '>=', date_start))
            if date_end:
                args.append((date_field, '<=', date_end))
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
        model = self.env[WORKDIST_MODELNAME].search(
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
