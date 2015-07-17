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

STRATEGIES_SELECTION = {
    'uniform': {'name': 'Uniform Distribution', 'other_fields': []},
    'effort': {'name': 'Effort Based Distribution',
               'other_fields': []},
    'effort_month': {'name': 'Next Month Effort Based Distribution',
                     'other_fields': ['date_start']},
}

FIELD_NAME_TO_SHOW_ON_WIZARD = \
    lambda model: 'x_%s_ids' % model.replace('.', '_')

WIZARD_NAME = 'work.distributor.wizard'


def _evaluate_domain(env, model, domain_str):
    ''' Pop user lang information from context to allow put in domain names
    and search always on original text and not on user lang translations.

    '''
    domain = safe_eval(domain_str or '[]')
    context = dict(env.context)
    context.pop('lang', False)
    return env[model].with_context(context).search(domain)


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
    group_model = fields.Char('Group Model')
    domain = fields.Text(help='Odoo domain to search in destination_field`s '
                              'model.')
    domain_field = fields.Many2one(
        'ir.model.fields', 'Domain Field',
        help='Field that it value determine domain of '
             'distribution destination.')
    destination_field = fields.Many2one(
        'ir.model.fields', 'Destination Field', required=True,
        help='Field that it value it will determinate by distribution '
             'strategy apply.')
    destination_model = fields.Char('Destination Model')
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
    action = fields.Many2one('ir.actions.act_window', required=True)
    strategy_field = fields.Many2one('ir.model.fields', 'Setting Field',
                                     required=True)

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

    @api.constrains('domain')
    def _check_domain(self):
        for model in self:
            try:
                if not _evaluate_domain(self.env,
                                        model.destination_field.relation,
                                        model.domain):
                    raise ValidationError(
                        _('Domain evaluate not return any record.'))
            except:
                raise ValidationError(_('Domain value are wrong.'))
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
    @api.onchange('group_field')
    def onchange_group_field(self):
        if self.group_field:
            self.group_model = self.group_field.relation
        else:
            self.group_model = False

    @api.model
    @api.onchange('destination_field')
    def onchange_destination_field(self):
        if self.destination_field:
            self.destination_model = self.destination_field.relation
        else:
            self.destination_model = False

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
                strategy.apply(item, values, **dict(other_fields))
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
        action = self.create_actions(group_field.relation, model.name,
                                     destination_field.name, strategy_field)
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
        name = ("Define work Distribution Strategy for %s field of %s "
                "model" % (destination_field, model_name or ''))
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

    def write(self, values):
        raise Warning(_('Error!'),
                      _('This items are not ables to update, you must '
                        'delete and create a new one.'))


class WorkDistributionStrategy(models.Model):
    _name = 'work.distribution.strategy'

    name = fields.Selection([(k, v.get('name', ''))
                             for k, v in STRATEGIES_SELECTION.items()],
                            required=True)

    _sql_constraints = [
        ('name_unique', 'unique (name)', 'Strategy must be unique!')
    ]

    @api.one
    def apply(self, dist_model, values, **kwargs):
        method = getattr(self, self.name, None)
        candidates = False
        if bool(dist_model.group_field):
            g_id = values.get(dist_model.group_field.name, False)
            if g_id:
                candidates = getattr(
                    self.env[dist_model.group_field.relation].browse(g_id),
                    dist_model.domain_field.name, False
                )
        elif dist_model.domain:
            candidates = _evaluate_domain(
                self.env, dist_model.destination_field.relation,
                dist_model.domain)
        if method and candidates:
            method(dist_model, candidates, values, **kwargs)

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
        last_dist = last_dist[0] or 0
        next_dist = (
            min(_id for _id in candidates.ids if _id > last_dist)
            if last_dist and any(_id > last_dist
                                 for _id in candidates.ids)
            else candidates.ids[0]
        )
        values.update({dist_model.destination_field.name: next_dist})
        return values

    def effort(self, dist_model, candidates, values, **kwargs):
        values.update({
            dist_model.destination_field.name:
                self._effort(dist_model, candidates, values)
        })

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
        values.update({dist_model.destination_field.name: self._effort(
            dist_model, candidates, values, date_field=date_field.name,
            date_start=strlow_date, date_end=strupp_date)})

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

    @api.model
    def get_fields_name(self, mixed=True):
        result = []
        method = getattr(result, 'extend' if mixed else 'append')
        for strategy in self:
            method(STRATEGIES_SELECTION.get(
                strategy.name, {}).get('other_fields'))
        return set(result) if mixed else result


class WorkDistributorWizard(models.TransientModel):
    _name = WIZARD_NAME

    name = fields.Char()
    strategy_id = fields.Many2one(
        'work.distribution.strategy', 'Strategy',
        help='Strategy of work distribution to apply to this items.')
    info = fields.Text()

    @api.model
    def default_get(self, fields_list):
        values = super(WorkDistributorWizard, self).default_get(fields_list)
        if 'info' in fields_list:
            active_ids = self.env.context.get('active_ids', False)
            active_model = self.env.context.get('active_model', False)
            ir_model = self.env['ir.model']
            model = ir_model.search([('model', '=', active_model)])[0]
            names = [n for i, n in self.env[active_model].browse(
                active_ids).name_get()]
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
