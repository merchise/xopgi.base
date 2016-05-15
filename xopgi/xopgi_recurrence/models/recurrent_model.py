# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# xopgi_recurrence.models.recurrent_model
# ----------------------------------------------------------------------
# Copyright (c) 2013 - 2016 Merchise Autrement
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2014-11-29

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

import operator
from operator import itemgetter

from openerp import SUPERUSER_ID
from openerp.osv import osv, fields
from openerp.tools.translate import _

from dateutil import rrule
from datetime import datetime, timedelta

from six import string_types

from xoutil.types import is_collection
from xoeuf.osv import datetime_user_to_server_tz
from xoeuf.tools import normalize_datetime as normalize_dt
from xoeuf.tools import normalize_date as normalize_date
from xoeuf.tools import normalize_datetimestr as normalize_dt_str
from xoeuf.tools import normalize_datestr as normalize_d_str

OPERATORS = {
    '<': operator.lt,
    '<=': operator.le,
    '>': operator.gt,
    '>=': operator.ge,
    '=': operator.eq,
    '!=': operator.ne,
    '==': operator.eq,
    '<>': operator.ne,
}


FREQ = [('daily', 'Day(s)'), ('weekly', 'Week(s)'), ('monthly', 'Month(s)'),
        ('yearly', 'Year(s)')]
END_TYPE = [('no_end_date', 'No end date'), ('until', 'Until'),
            ('count', 'Number of repetitions')]
BYWEEKDAY = [('n', 'Every'), ('1', 'The First'), ('2', 'The Second'),
             ('3', 'The Third'), ('4', 'The Fourth'), ('5', 'The Fifth'),
             ('-1', 'The Last')]
MONTHS = [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
          ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
          ('9', 'September'), ('10', 'October'), ('11', 'November'),
          ('12', 'December')]
_DAY_HOURS = 24
_HOUR_SECONDS = 3600
_V_DATE_FORMAT = "%Y%m%dT%H%M%S"


def _required_field(field='A field'):
    raise osv.except_osv(_('Error!'), field + _(' is required.'))


class recurrent_model(osv.osv):
    _name = 'recurrent.model'
    _description = 'Recurrent model'

    def _get_date(self, cr, uid, ids, field, arg, context=None):
        ''' Get the init datetime of recurrent object of given ids,
            using the user timezone.
        '''
        if not context:
            context = {}
        result = {}
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        _date = lambda date: (datetime_user_to_server_tz(cr, uid, date,
                                                         context.get('tz')))
        for item in self.browse(cr, uid, ids, context=context):
            # más una hora para evitar el problema con el horario de verano.
            date_from = normalize_dt(item.date_from) + timedelta(hours=1)
            result[item.id] = normalize_dt_str(_date(date_from))
        return result

    def _date_search(self, cr, uid, obj, name, args, context=None):
        """Get the domain args to search the real and virtual occurrences
        related with the original args.

        First: change the 'date' field to 'date_from'

        Second: On recurrent instances no apply condition 'date' > or >=
        on a date
        """
        new_arg = args[0]
        res = []
        if new_arg and len(new_arg) > 2:
            if new_arg[1] in ['>', '>=']:
                res.extend(['|', ('is_recurrent', '=', 1)])
            res.append(('date_from', new_arg[1], new_arg[2]))
        return res

    def _get_duration(self, cr, uid, ids, field, arg, context=None):
        ''' Get the duration on hours of recurrent object of given ids.

        '''
        result = {}
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        # Menos 2 para evitar problemas con el horario de verano esto
        # permite tener instancias desde la 1AM hasta las 11PM en caso
        # de cambio de uso horario sigue viendose en el mismo día.
        _duration_hours = lambda days: (days * _DAY_HOURS - 2)
        for item in self.browse(cr, uid, ids, context=context):
            if item.duration:
                result[item.id] = _duration_hours(item.duration)
            elif item.date_to:
                df = normalize_date(item.date_from)
                dt = normalize_date(item.date_to)
                result[item.id] = (dt - df).total_seconds() / _HOUR_SECONDS
            else:
                result[item.id] = 1
        return result

    _columns = {
        # Basic datas.
        'name': fields.char('Name', size=254),
        'date_from': fields.date('Init date', help='Date to be init.',
                                 required=True),
        'date': fields.function(_get_date, method=True,
                                string='Date and time to be init.',
                                type='datetime', fnct_search=_date_search,
                                help='Init date and time on user time zone.'),
        'date_to': fields.date('End date', help='Date to be end.'),
        'duration': fields.integer('Duration', help='Duration on days.'),
        'calendar_duration': fields.function(_get_duration, method=True,
                                             string='Duration', type='float'),
        'allday': fields.boolean('All Day'),
        'description': fields.text('Description'),
        'active': fields.boolean('Active'),
        # General recurrence data.
        'is_recurrent': fields.boolean('Is recurrent', help='Check if is '
                                                            'recurrent.'),
        'rrule': fields.char('RRULE', size=124, readonly=True),
        'freq': fields.selection(FREQ, 'Frequency type'),
        'interval': fields.integer('Repeat Every', help="Repeat every "
                                                        "(Days/Week/Month/"
                                                        "Year)"),
        # Recurrence by week data.
        'mo': fields.boolean('Monday'),
        'tu': fields.boolean('Tuesday'),
        'we': fields.boolean('Wednesday'),
        'th': fields.boolean('Thursday'),
        'fr': fields.boolean('Friday'),
        'sa': fields.boolean('Saturday'),
        'su': fields.boolean('Sunday'),
        # Recurrence by month data.
        'days_option': fields.selection([('week_day', 'By week day'),
                                         ('month_day', 'By month day')],
                                        'Option'),
        'monthly_day': fields.integer('Days of month'),
        'by_week_day': fields.selection(BYWEEKDAY, 'Reference'),
        # Recurrence by year data.
        'months': fields.selection(MONTHS, 'Month'),
        'is_easterly': fields.boolean('By easter', help='A date from '
                                                        'western easter '
                                                        'sunday.'),
        'byeaster': fields.integer('By easter', help='Number of days '
                                                     'from western easter '
                                                     'sunday.'),
        # Ending data
        'end_type': fields.selection(END_TYPE, 'Recurrence Termination'),
        'count': fields.integer('Repeat', help="Repeat x times"),
        'until': fields.date('Repeat Until'),
    }

    _defaults = {
        'is_recurrent': True,
        'rrule': '',
        'freq': 'daily',
        'interval': 1,
        'days_option': 'month_day',
        'by_week_day': 'n',
        'months': str(datetime.today().month),
        'monthly_day': datetime.today().day,
        'date_from': normalize_d_str(datetime.today()),
        'allday': True,
        'duration': 1,
        'end_type': 'no_end_date',
        'count': 5,
        'byeaster': 0,
        'active': True,
    }

    @staticmethod
    def parse_until_date(until, context=None):
        '''Set of 11PM hour of day on UTC

        '''
        end_date_new = normalize_dt(until).replace(hour=23)
        return end_date_new.strftime(_V_DATE_FORMAT)

    def _compute_rule_string(self, data, context=None):
        """Compute rule string according to value type RECUR of iCalendar
        from the values given.

        @param data: dictionary of freq and interval value

        @return: string containing recurring rule (empty if no rule)

        """
        def get_BYDAY_string(freq, data):
            '''Compose the 'BYDAY' param for rrule

            '''
            weekdays = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']
            day_option = data['days_option']
            if freq == 'weekly' or (freq == 'monthly' and
                                    day_option == 'week_day') or \
                                   (freq == 'yearly' and
                                    day_option == 'week_day' and
                                    not data.get('is_easterly')):
                by_week_day = (freq != 'weekly'
                               and data.get('by_week_day', '') != ''
                               and data.get('by_week_day', '') or '')
                byday = [by_week_day + weekday.upper()
                         for weekday, val in data.items()
                         if val and weekday in weekdays]
                if byday:
                    return ';BYDAY=' + ','.join(byday)
                _required_field('At least a weekday')
            return ''

        def get_BYMONTHDAY_string(freq, data):
            '''Compose the 'BYMONTHDAY' param for rrule

            '''
            if freq == 'monthly' or (freq == 'yearly' and not
                                     data.get('is_easterly')):
                days_option = data.get('days_option', '')
                monthly_day = data.get('monthly_day', 0)
                if not days_option:
                    _required_field('An option')
                if days_option == 'month_day':
                    if not monthly_day:
                        _required_field('At least a month date')
                    if -31 <= int(monthly_day) <= 31:
                        return ';BYMONTHDAY=' + str(monthly_day)
                    else:
                        raise ValueError()
            return ''

        def get_BYEASTER_string(freq, data):
            '''Compose the 'BYEASTER' param for rrule

            '''
            if freq == 'yearly':
                if data.get('is_easterly'):
                    byeaster = data.get('byeaster', 0)
                    if not (-365 <= int(byeaster) <= 365):
                        raise ValueError()
                    return ';BYEASTER=' + str(data.get('byeaster', '0'))
                elif data.get('days_option', '') == 'month_day':
                    if not data.get('months'):
                        _required_field('Month')
                    return ';BYMONTH=' + str(data.get('months')) or ''
            return ''

        def get_end_date(data):
            '''Compose the 'UNTIL' or 'COUNT' param for rrule

            '''
            end_type = data.get('end_type')
            if end_type == 'count':
                return ';COUNT=' + str(data.get('count')) or ''
            until = data.get('until')
            if until and end_type == 'until':
                end_date = self.parse_until_date(until, context)
                return ';UNTIL=' + end_date or ''
            return ''

        freq = data.get('freq', False)
        res = ''
        if freq:
            interval = data.get('interval')
            template = 'FREQ={freq}{interval}{end_date}{by}{easter}'
            res = template.format(
                freq=freq.upper(),
                interval=(';INTERVAL=%s' % interval if interval else ''),
                end_date=get_end_date(data),
                by=get_BYDAY_string(freq, data) or get_BYMONTHDAY_string(freq, data),
                easter=get_BYEASTER_string(freq, data)
            )
        return res

    def _check_dates(self, virtual_dates, data, args):
        '''Check every occurrence date for domain args referent to date.

        :param virtual_dates: List of date to check.
        :param data: List of dict with all fields values.
        :param args: Domain to check.
        :return: Filtered list of dict with all fields values.
        '''
        result_data = []
        for r_date in virtual_dates:
            pile = []
            for arg in args:
                if arg[0] in ('date', 'date_from', 'date_to'):
                    op = OPERATORS[arg[1]]
                    ok = op(r_date, normalize_dt(arg[2]))
                    pile.append(ok)
                elif str(arg) == str('&') or str(arg) == str('|'):
                    pile.append(arg)
                else:
                    pile.append(True)
            pile.reverse()
            new_pile = []
            for val in pile:
                if not isinstance(val, string_types):
                    res = val
                elif str(val) == str('&'):
                    first = new_pile.pop()
                    second = new_pile.pop()
                    res = first and second
                elif str(val) == str('|'):
                    first = new_pile.pop()
                    second = new_pile.pop()
                    res = first or second
                new_pile.append(res)
            if not any(True for val in new_pile if not val):
                r_date_str = normalize_dt_str(r_date)
                idval = self.real_id2virtual(data.get('id'), r_date_str)
                result_data.append(dict(data, id=idval, date=r_date_str))
        return result_data

    def _sort(self, data, order):
        '''Sort the list of items by order specs.

        :return:List of ids sorted by order specs.
        '''
        def comparer(left, right):
            from xoutil.types import are_instances
            for fn, sign in comparers:
                leftres = fn(left)
                rightres = fn(right)
                if are_instances(leftres, rightres, tuple):
                    # comparing many2one values, sorting on name_get
                    # result
                    leftv, rightv = leftres[1], rightres[1]
                else:
                    leftv, rightv = leftres, rightres
                return sign * cmp(leftv, rightv)
            return 0
        comparers = [(itemgetter(field), -1 if spec == 'desc' else 1) for
                     field, spec in order]
        result = [r['id'] for r in sorted(data, cmp=comparer)]
        return result

    def _set_end(self, cr, uid, rule_str, domain, offset, limit, context=None):
        '''Force to end for non infinitive search.

        '''
        context = context if context else {}
        for arg in domain:
            if arg[0] in ('date', 'date_from', 'date_to') and arg[1] in ['<', '<=']:
                until = normalize_dt(arg[2])
                until = datetime_user_to_server_tz(cr, uid, until,
                                                   tz_name=context.get('tz'))
                until = normalize_d_str(until)
                rule_str += ';UNTIL=' + self.parse_until_date(until, context)
                return rule_str
        rule_str += ';COUNT=' + str(offset + (limit or 100))
        return rule_str

    def _get_virtuals_ids(self, cr, uid, ids, domain, offset=0, limit=100,
                          context=None):
        """Gives virtual event ids for recurring events based on value of
        Recurrence Rule
        This method gives ids of dates that comes between start date and
        end date of calendar views

        @param limit: The Number of Results to Return

        """
        from six import string_types
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        result_data = []
        extra_fields = ['date', 'rrule', 'is_recurrent']
        order = context.get('order', None) or self._order
        order = order.split(',') if order else []
        order_specs = [
            (field.split()[0], field.split()[-1].lower())
            for field in order
        ]
        order_fields = [field for field, _ in order_specs]
        fields = list(set(extra_fields + order_fields))
        super_read = super(recurrent_model, self).read
        for item in super_read(cr, uid, ids, fields, context=context):
            if not item['is_recurrent'] or isinstance(item['id'], string_types):
                result_data.append(item)
                rule_str = False
            elif not item['rrule']:
                rule_str = self._get_rulestring(cr, uid, item['id'],
                                                context=context)
                rule_str = rule_str[item['id']]
            else:
                rule_str = item['rrule']
            if rule_str:
                if rule_str.find('COUNT') < 0 and rule_str.find('UNTIL') < 0:
                    rule_str = self._set_end(cr, uid, rule_str, domain,
                                             offset, limit,
                                             context=context)
                date = normalize_dt(item['date'])
                recurrent_dates = self._get_recurrent_dates(str(rule_str),
                                                            startdate=date)
                result_data.extend(self._check_dates(recurrent_dates, item,
                                                     domain))
        if order:
            result = self._sort(result_data, order_specs)
        else:
            result = [data.get('id') for data in result_data]
        if limit and len(result) >= limit:
            return result[0:limit]
        return result

    def _get_recurrent_dates(self, rrulestring, startdate=None):
        '''call rrule.rrulestr for list of occurrences dates

        :param rrulestring:
        :param startdate:
        :return:
        '''
        if not startdate:
            startdate = datetime.now()
        result = rrule.rrulestr(str(rrulestring), dtstart=startdate,
                                forceset=True)
        return list(result)

    def real_id2virtual(self, real_id, recurrent_date):
        """ Convert a real id (type int) into a "virtual id" (type string).

        E.g. real event id is 1 and recurrent_date
        is set to 01-12-2009 10:00:00, so it will return 1-20091201100000.

        """
        if real_id and recurrent_date:
            recurrent_date = normalize_dt(recurrent_date)
            recurrent_date = recurrent_date.strftime(_V_DATE_FORMAT)
            return '%d-%s' % (real_id, recurrent_date)
        return real_id

    def _virtual_id2real(self, virtual_id=None, with_date=False):
        """ Convert a "virtual id" (type string) into a real id (type int).

        E.g. virtual/recurring event id is 4-20091201100000, so
        it will return 4.

        @param with_date: if a value is passed to this param it will
        return dates based on value of withdate + base_calendar_id

        @return: real id or real id, date

        """
        if virtual_id and isinstance(virtual_id, (str, unicode)):
            res = virtual_id.split('-')
            if len(res) >= 2:
                real_id = res[0]
                if not with_date:
                    return real_id
                start = datetime.strptime(res[1], _V_DATE_FORMAT)
                end = start + timedelta(hours=with_date)
                start = normalize_dt_str(start)
                end = normalize_dt_str(end)
                return int(real_id), start, end
        return virtual_id

    def _update_rrule(self, cr, uid, ids, context=None):
        res_rrules = self.get_rulestring(cr, uid, ids, context=context)
        if not res_rrules:
            return False
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        for i in ids:
            self.write(cr, uid, i, {'rrule': res_rrules[i]}, context=context)
        return res_rrules

    def _check_for_one_occurrency_change(self, cr, uid, ids, context=None):
        '''

        :raise an except_osv if one of ids is virtual
        :param ids:
        :return:
        '''
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        real_id_vs_virtual = map(lambda x: (x, self._virtual_id2real(x)), ids)
        real_ids = [real_id for virtual_id, real_id in real_id_vs_virtual]
        if real_ids != ids:
            raise osv.except_osv(_('Error!'), _('An occurrence of an '
                                                'recurrent rule can`t '
                                                'be modify or deleted.'))

    def get_rulestring(self, cr, uid, ids, context=None):
        """Gets Recurrence rule string according to value type RECUR of
        iCalendar from the values given.

        @param ids: List of calendar event's ids.

        @return: dictionary of rrule value.

        """
        result = {}
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        # Browse these fields as SUPERUSER because if the record is
        # private a normal search could return False and raise an error.
        for item in osv.osv.read(self, cr, SUPERUSER_ID, ids, [],
                                 context=context):
            if item:
                if not item.get('freq'):
                    _required_field('Frequency')
                if (item['interval'] or 0) < 0:
                    raise osv.except_osv(_('Warning!'), _('Interval cannot '
                                                          'be negative.'))
                if (item['count'] or 0) <= 0:
                    raise osv.except_osv(_('Warning!'), _('Count cannot be '
                                                          'negative or 0.'))
                if item['is_recurrent']:
                    result[item['id']] = self._compute_rule_string(item,
                                                                   context)
                else:
                    result[item['id']] = ''
        return result

    def is_occurrency(self, cr, uid, ids, day, context=None):
        '''Get True if day(date) is on one of virtuals ocurrences of real
        [ids] else False

        :param ids: real ids where search
        :param day: date to search
        :return: True or False
        '''
        day = datetime_user_to_server_tz(cr, uid, normalize_dt(day),
                                         context.get('tz'))
        day_str = normalize_dt_str(day.replace(hour=23, minute=59))
        res_ids = self.search(cr, uid, [('id', 'in', ids),
                                        ('date', '<=', day_str)],
                              context=context)
        for data in self.read(cr, uid, res_ids, ['date', 'calendar_duration'],
                              context=context):
            d_from = normalize_dt(data['date'])
            d_to = d_from + timedelta(hours=data.get('calendar_duration'))
            if d_from.date() <= day.date() <= d_to.date():
                return True
        return False

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
               context=None, count=False):
        """if 'virtual_id' not in context or are False then normally
        search, else search virtual occurrences and return then.

        """
        if context is None:
            context = {}
        _super = super(recurrent_model, self).search
        res = _super(cr, uid, args, offset=offset, limit=limit,
                     order=order, context=context, count=False)
        if not res:
            return []
        if context.get('virtual_id', True):
            res = self._get_virtuals_ids(cr, uid, res, args, offset, limit,
                                         context=context)
        if count:
            return len(res)
        elif limit:
            return res[offset:offset + limit]
        return res

    def read(self, cr, uid, ids, fields=None, context=None,
             load='_classic_read'):
        """Return the list of dict with the [fields].
          if [ids] contain virtual ids read data from real ids and create
          virtual copies to return

        """
        _super = super(recurrent_model, self).read
        if not context.get('virtual_id', True):
            return _super(cr, uid, ids, fields,
                          context=context,
                          load=load)
        if not ids:
            return []
        w_ids = ids if is_collection(ids) else [ids]
        fields2 = fields[:] if fields else []
        targets = ('date', 'date_from', 'date_to')
        has_dates = any(field in fields for field in targets)
        if fields and 'calendar_duration' not in fields and has_dates:
            fields2.append('calendar_duration')
        ids_index = {int(self._virtual_id2real(id)): id
                     for id in w_ids if id}
        real_ids = ids_index.keys()
        # XXX: super read may call _name_get, that in turns calls
        # self.read leading to recursion... Pass virtual_id = False to
        # bail out.
        cpcontex = dict(context or {}, virtual_id=False)
        real_data = _super(cr, uid, real_ids, fields2, context=cpcontex,
                           load=load)
        real_data = {row['id']: row for row in real_data}
        result = []
        for real_id, virtual_id in ids_index.items():
            res = real_data.get(real_id, {}).copy()
            if has_dates:
                ls = self._virtual_id2real(virtual_id,
                                           with_date=res.get(
                                               'calendar_duration') or 23)
                if is_collection(ls) and len(ls) >= 2:
                    if res.get('date_from'):
                        res['date_from'] = normalize_d_str(ls[1])
                    if res.get('date'):
                        res['date'] = normalize_dt_str(ls[1])
                    if res.get('date_to'):
                        res['date_to'] = normalize_d_str(ls[2])
            res['id'] = virtual_id
            result.append(res)
        if fields and 'calendar_duration' not in fields:
            for r in result:
                r.pop('calendar_duration', None)
        if not hasattr(ids, '__iter__'):
            return result[0] if result else []
        return result

    def unlink(self, cr, uid, ids, context=None):
        # TODO: implement the logic for rule exceptions and one occurrence
        # modifications.
        self._check_for_one_occurrency_change(cr, uid, ids, context)

        result = super(recurrent_model, self).unlink(cr, uid, ids,
                                                     context=context)
        return result

    def write(self, cr, uid, ids, values, context=None):
        # TODO: implement the logic for rule exceptions and one occurrence
        # modifications.
        context = context or {}
        self._check_for_one_occurrency_change(cr, uid, ids, context)
        res = super(recurrent_model, self).write(cr, uid, ids, values,
                                                 context=context)
        if 'no_update_rrule' not in context and not values.get('rrule'):
            self._update_rrule(cr, uid, ids, context=context)
        return res

    def create(self, cr, uid, values, context=None):
        id = super(recurrent_model, self).create(cr, uid, values,
                                                 context=context)
        self._update_rrule(cr, uid, id, context=context)
        return id

    def next_date(self, rrulestring, dt=False, include=False):
        """Returns the first recurrence after the given datetime instance.

        :param rrulestring:
        :param dt: start date or None to use now().
        :param include: defines what happens if dt is an occurrence. With
        include=True, if dt itself is an occurrence, it will be returned.
        :return: next occurrence datetime.
        """
        if not dt:
            dt = datetime.now()
        rule = rrule.rrulestr(str(rrulestring), dtstart=dt, forceset=True)
        return rule.after(dt, include)
