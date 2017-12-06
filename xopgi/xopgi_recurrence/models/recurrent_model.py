# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# xopgi_recurrence.models.RecurrentModel
# ----------------------------------------------------------------------
# Copyright (c) 2013-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

import operator
from operator import itemgetter

from xoeuf.odoo import api, models, fields, exceptions, _
from dateutil import rrule
from datetime import datetime, timedelta

from six import string_types
from xoutil.future.types import is_collection

from xoeuf.osv import datetime_user_to_server_tz
from xoeuf.tools import normalize_datetime as normalize_dt
from xoeuf.tools import normalize_date
from xoeuf.tools import normalize_datetimestr as normalize_dt_str
from xoeuf.tools import normalize_datestr as normalize_d_str


def _SEARCH_DOWNGRADE(self, value, args, offset=0, limit=None, order=None,
                      count=False):
    return list(value.ids) if not count else value


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

_HOURS_PER_DAY = 24
_SECS_PER_HOUR = 3600
_V_DATE_FORMAT = "%Y%m%dT%H%M%S"


def _required_field(field='A field'):
    raise exceptions.except_orm(_('Error!'), field + _(' is required.'))


class RecurrentModel(models.AbstractModel):
    '''A mixin for recurrent things (in time).

    It's very similar of recurrence in the calendar module, with some
    adjustments.

    ``recurrent.model`` defines fields use to define the conditions in a
    timeline and the recurrence rules (to see module :mod:`dateutil.rrule`) in
    which a given activity can occur.

    You can declare a recurrence in a time interval -'Repeat every' for example:

    Recurrent pattern:
    Repeat every: 1  (Days/Week/Month/Year)

    You can also state how often, days of the week, days of the month or at
    what time of year the recurrence may occur, for example:

    class MyMeeting(Model):
        _name = 'my.meeting'
        _inherit = [_name, 'recurrent.model']

    >>> Meeting = self.env['my.meeting']

    # Case 1:Repeat once every day
    >>> meeting = Meeting.create(interval=1, freq='daily', end_type='no_end_date')

    # Case 2:Repeat each week on Mondays and Fridays
    >>> meeting = Meeting.create(interval=1, freq='weekly', monday=True,
                                 friday=True, end_type='no_end_date')

    :attr monday:  Set this True to indicate that this event happen on Mondays.
    Attributes 'tuesday' and other week day names are similar to `monday`.

    # Case 3:Repeat each month the nth days Mondays and Fridays':
    >>> meeting = Meeting.create(interval=1, freq='monthly', days_option='week_day',
                                 monday=True, friday=True, end_type='no_end_date')


    # Case 4:Repeat each month the cardinal days of month:
    >>> meeting = Meeting.create(interval=1, freq='monthly',days_option='month_day',
                                 monthly_day=5, end_type='no_end_date',
                                 end_type='no_end_date')

    :attr monthly_day: Refers to the cardinal days of the month.

    # Repeat each year, similar to case three specifying that month of the year.
       >>> meeting = Meeting.create(interval=1, freq='yearly',days_option='month_day',
                                 monthly_day=5, months=1, end_type='no_end_date')
    :attr months: specify year month.

    # Repeat each year specifying number of days from western easter sunday.
       >>> meeting = Meeting.create(interval=1, freq='yearly',is_easterly=True,
                                 byeaster_day=-2, end_type='no_end_date')
    :attr byeaster: Number of days from western easter sunday by default is 0.

    # Recurrent Termination
    One recurrent by default is end_type='no_end_date' but this can to take other
    values:
    E.g. Value1: until='2017-03-04'
         Value2: count=5  Repeat recurrent event by x=5 times.

    '''

    _name = 'recurrent.model'
    _description = 'Recurrent model'

    @api.multi
    def _get_date(self):
        '''Get the values for the compute 'date' field of the recurrent object
        using the user timezone.This is calculated with the field 'date_from'.

        '''

        _date = lambda date: datetime_user_to_server_tz(
            self._cr, self._uid, date, self._context.get('tz'))
        for item in self:
            # Plus an hour to avoid the problem with daylight saving time.
            date_from = normalize_dt(item.date_from) + timedelta(hours=1)
            item.date = normalize_dt_str(_date(date_from))

    def _search_date(self, operator, value):
        """Get the domain to search for 'date'.

        We simply translate it to search by 'date_from'.

        """
        if value not in (False, None):
            # Some modules try to see if the date is not set by passing False.
            value = normalize_date(value)
        return [('date_from', operator, value)]

    @api.multi
    def _get_duration(self):
        '''Get the values on hours to the compute field 'calendar_duration'  of
        recurrent object.

        '''
        for item in self:
            # By default 'duration = 1 day'
            if item.duration:
                # Minus 2 to avoid problems with daylight savings. This allows
                # to have instances from 1AM to 11PM in case change of use
                # schedule is still on the same day.
                item.calendar_duration = item.duration * _HOURS_PER_DAY - 2
            elif item.date_to:
                df = normalize_date(item.date_from)
                dt = normalize_date(item.date_to)
                item.calendar_duration = (dt - df).total_seconds() / _SECS_PER_HOUR
            else:
                item.calendar_duration = 1

    # Basic datas.
    date_from = fields.Date(
        'Initial date',
        required=True,
        default=normalize_d_str(datetime.today()),
        help='Date to be init of recurrence'
    )

    date = fields.Datetime(
        compute=_get_date,
        search=_search_date,
        method=True,
        string='Date and time for representation in calendar views',
    )

    date_to = fields.Date(
        'Final date',
        help='Date to be end the recurrence'
    )

    duration = fields.Integer(
        'Duration',
        default=1,
        help='Duration on days of the recurrence'
    )

    calendar_duration = fields.Float(
        compute='_get_duration',
        method=True,
        string='Duration',
        help='Get the duration on hours of the recurrence'
    )

    allday = fields.Boolean(
        'All Day',
        default=True
    )

    active = fields.Boolean(
        'Active',
        default=True,
        help='Indicate if recurrent object is active or not'
    )

    # General recurrence data.
    is_recurrent = fields.Boolean(
        'Is recurrent',
        default=True,
        help='Check if is recurrent.'
    )

    rrule = fields.Char(
        'RRULE',
        size=124,
        readonly=True,
        default='',
        help='This field is update after to creates or to update the recurrent'
             ' model by the function  _update_rrule. By default it is taken'
             ' value but then it is calculated and takes a similar value.'
             ' E.g. rrule=FREQ=WEEKLY;INTERVAL=1;BYDAY=TU,MO'
    )

    freq = fields.Selection(
        FREQ,
        'Frequency type',
        default='daily',
        # XXX: Don't put this, because there's an error in the JS client that
        # messes up with the invisible toggling we have there.
        # help='Frecuency type (Daily/Weekly/Monthly/Yearly)'
    )

    interval = fields.Integer(
        'Repeat Every',
        default=1,
        help='Repeat every (Days/Week/Month/Year)'
    )

    # Recurrence by week data.
    mo = fields.Boolean(
        'Monday',
        help="Indicate if the week's day 'Monday' is include or not for the"
             " recurrence pattern"
    )

    tu = fields.Boolean(
        'Tuesday',
        help="Indicate if the week's day 'Tuesday' is include or not for the"
             " recurrence pattern"
    )

    we = fields.Boolean(
        'Wednesday',
        help="Indicate if the week's day 'Wednesday' is include for the"
             " recurrence pattern"
    )

    th = fields.Boolean(
        'Thursday',
        help="Indicate if the week's day 'Thursday' is include for the"
             " recurrence pattern"
    )

    fr = fields.Boolean(
        'Friday',
        help="Indicate if the week's day 'Friday' is include for the"
             " recurrence pattern"
    )

    sa = fields.Boolean(
        'Saturday',
        help="Indicate if the week's day 'Saturday' is include for the"
             " recurrence pattern"
    )

    su = fields.Boolean(
        'Sunday',
        help="Indicate if the week's day 'Sunday' is include for the"
             " recurrence pattern"
    )

    # Recurrence by month data.
    days_option = fields.Selection([
        ('week_day', 'By week day'),
        ('month_day', 'By month day')],
        'Option',
        default='month_day',
        help='Indicates the days of the week: E.g.(Mo, Tu, We, Th, Fr, Sa, Su) or'
             ' indicates the days of the month'
    )

    monthly_day = fields.Integer(
        'Days of month',
        default=datetime.today().day
    )

    by_week_day = fields.Selection(
        BYWEEKDAY,
        'Reference',
        default='n',
        help="Selection by week's days E.g.(Every, The First, The Second, The Third,"
             " The Fourth, The Fifth, The Last)"
    )

    # Recurrence by year data.
    months = fields.Selection(
        MONTHS,
        'Month',
        deafault=str(datetime.today().month),
        help='Allow to select month of year'
    )

    is_easterly = fields.Boolean(
        'By easter',
        help='A date from western easter sunday.'
    )

    byeaster = fields.Integer(
        'By easter',
        default=0,
        help='Number of days from western easter sunday.'
    )

    # Ending data
    end_type = fields.Selection(
        END_TYPE,
        'Recurrence Termination',
        default='no_end_date',
        help='Selection by recurrence termination'
    )

    count = fields.Integer(
        'Repeat',
        default=5,
        help='Repeat recurrent event by x times'
    )

    until = fields.Date(
        'Repeat Until',
        help='Date end for the recurrent termination'
    )

    @staticmethod
    def parse_until_date(until):
        '''Set of 11PM hour of day on UTC

        '''
        end_date_new = normalize_dt(until).replace(hour=23)
        return end_date_new.strftime(_V_DATE_FORMAT)

    def _compute_rule_string(self, data):
        '''Compute rule string according to value type RECUR of iCalendar
        from the values given.

        @param data: dictionary of freq and interval value

        @return: string containing recurring rule (empty if no rule)

        '''
        def get_BYDAY_string(freq, data):
            '''Compose the 'BYDAY' and params for rrule.

            If in BYDAY not is specificate 'n', means every  week's day. E.g.
            BYDAY={}MO,{}TU If 'n' can take values(n,1..5,-1).
            The First Monday and Tuesday is equal: E.g.BYDAY={1}MO,{1}TU
            To see module :mod:`dateutil.rrule`

            '''
            weekdays = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']
            day_option = data['days_option']
            if freq == 'weekly' or (freq == 'monthly' and
                                    day_option == 'week_day') or \
                                   (freq == 'yearly' and
                                    day_option == 'week_day' and
                                    not data.get('is_easterly')):
                by_week_day = (freq != 'weekly' and
                               data.get('by_week_day', '') != 'n' and
                               data.get('by_week_day', '') or '')
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
                else:
                    if not data.get('months'):
                        _required_field('Month')
                    return ';BYMONTH=' + str(data.get('months')) or ''
            return ''

        def get_end_date(data):
            '''Concatenate the string rule to the field 'rrule'. Compose the 'UNTIL'
            or 'COUNT' param.

            '''
            end_type = data.get('end_type')
            if end_type == 'count':
                return ';COUNT=' + str(data.get('count')) or ''
            until = data.get('until')
            if until and end_type == 'until':
                end_date = self.parse_until_date(until)
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
                elif str(arg) in ('&', '|'):
                    pile.append(arg)
                else:
                    pile.append(True)
            pile.reverse()
            new_pile = []
            for val in pile:
                if not isinstance(val, string_types):
                    res = val
                elif str(val) == '&':
                    first = new_pile.pop()
                    second = new_pile.pop()
                    res = first and second
                elif str(val) == '|':
                    first = new_pile.pop()
                    second = new_pile.pop()
                    res = first or second
                new_pile.append(res)
            if not any(True for val in new_pile if not val):
                r_date_str = normalize_dt_str(r_date)
                # Get virtual_id with id and date E.g. 19-20170830T230000
                idval = self.real_id2virtual(data.get('id'), r_date_str)
                result_data.append(dict(data, id=idval, date=r_date_str))
        return result_data

    def _sort(self, data, order):
        '''Sort the list of items by order specs.

        :return:List of ids sorted by order specs.
        '''
        def comparer(left, right):
            from xoutil.future.types import are_instances
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
        # Return virtual_id with order specify E.g.['19-20170830T230000'...]
        result = [r['id'] for r in sorted(data, cmp=comparer)]
        return result

    @api.model
    def _set_end(self, rule_str, domain, offset, limit):
        '''Force to end for non infinitive search.

        '''
        for arg in domain:
            if arg[0] in ('date', 'date_from', 'date_to') and arg[1] in ['<', '<=']:
                until = normalize_dt(arg[2])
                until = datetime_user_to_server_tz(self._cr, self._uid, until,
                                                   tz_name=self._context.get('tz'))
                until = normalize_d_str(until)
                rule_str += ';UNTIL=' + self.parse_until_date(until)
                return rule_str
        rule_str += ';COUNT=' + str(offset + (limit or 100))
        return rule_str

    @api.multi
    def _get_virtuals_ids(self, domain, offset=0, limit=100):
        '''Gives virtual event ids for recurring events based on value of
        Recurrence Rule.

        Read the actual recurring models that you pass and according to the
        'rrule' of each of them returns the virtual_ids.

        This method gives ids of dates that comes between start date and
        end date of calendar views

        @param limit: The Number of Results to Return

        '''
        result_data = []
        extra_fields = ['date', 'rrule', 'is_recurrent']
        order = self._context.get('order', None) or self._order
        order = order.split(',') if order else []
        order_specs = [
            (field.split()[0], field.split()[-1].lower())
            for field in order
        ]
        order_fields = [field for field, _ in order_specs]
        fields = list(set(extra_fields + order_fields))
        for item in self.read(fields):
            if not item['is_recurrent'] or isinstance(item['id'], string_types):
                result_data.append(item)
                rule_str = False
            elif not item['rrule']:
                rule_str = self._get_rulestring(item['id'])
                rule_str = rule_str[item['id']]
            else:
                rule_str = item['rrule']
            if rule_str:
                if rule_str.find('COUNT') < 0 and rule_str.find('UNTIL') < 0:
                    # Add COUNT=100 for 'rule_str, if limit is not specify.
                    rule_str = self._set_end(rule_str, domain, offset, limit)
                date = normalize_dt(item['date'])
                # Get recurrent dates E.g. [datetime.datetime(2017, 8, 29, 23, 0)]
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
        '''Call rrule.rrulestr for list of occurrences dates

        :param rrulestring:
        :param startdate:
        :return:
        '''
        if not startdate:
            startdate = datetime.now()
        # Gets and verifies the rrule following RFC2445.
        result = rrule.rrulestr(str(rrulestring), dtstart=startdate,
                                forceset=True)
        return list(result)

    def real_id2virtual(self, real_id, recurrent_date):
        ''' Convert a real id (type int) into a "virtual id" (type string).

        E.g. real event id is 1 and recurrent_date
        is set to 01-12-2009 10:00:00, so it will return 1-20091201100000.

        '''
        if real_id and recurrent_date:
            recurrent_date = normalize_dt(recurrent_date)
            recurrent_date = recurrent_date.strftime(_V_DATE_FORMAT)
            return '%d-%s' % (real_id, recurrent_date)
        return real_id

    def _virtual_id2real(self, virtual_id=None, with_date=False):
        ''' Convert a "virtual id" (type string) into a real id (type int).

        E.g. virtual/recurring event id is 4-20091201100000, so
        it will return 4.

        @param with_date: if a value is passed to this param it will
        return dates based on value of withdate + base_calendar_id

        @return: real id or real id, date

        '''
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

    @api.multi
    def _update_rrule(self):
        '''Allow to call the calculation the string representing a rule:
        'rrule' and update the value by each recurrent model.

        '''
        res_rrules = self.get_rulestring()
        if not res_rrules:
            return False
        for item in self:
            item.write(res_rrules)
        return res_rrules

    @api.model
    def _check_for_one_occurrency_change(self):
        '''
        :raise an except_orm if one of ids is virtual
        :param ids:
        :return:
        '''
        real_id_vs_virtual = map(lambda x: (x, self._virtual_id2real(x)), self.ids)
        real_ids = [real_id for virtual_id, real_id in real_id_vs_virtual]
        if real_ids != self.ids:
            raise exceptions.except_orm(_('Error!'), _('An occurrence of an '
                                                       'recurrent rule can`t be'
                                                       'modify or deleted.'))

    @api.model
    def get_rulestring(self):
        """Gets Recurrence rule string according to value type RECUR of
        iCalendar from the values given.

        @param ids: List of calendar event's ids.

        @return: dictionary of rrule value.

        """
        result = {}
        # Browse these fields as SUPERUSER because if the record is
        # private a normal search could return False and raise an error.
        for item in self.sudo().read():
            if item:
                if not item.get('freq'):
                    _required_field('Frequency')
                if (item['interval'] or 0) < 0:
                    raise exceptions.except_orm(_('Warning!'), _('Interval cannot '
                                                                 'be negative.'))
                if (item['count'] or 0) <= 0:
                    raise exceptions.except_orm(_('Warning!'), _('Count cannot be '
                                                                 'negative or 0.'))
                if item['is_recurrent']:
                    result['rrule'] = self._compute_rule_string(item)
                else:
                    result['rrule'] = ''
        return result

    @api.multi
    def is_occurrency(self, day):
        '''Get True if day(date) is on one of virtuals ocurrences of real
        [ids] else False

        :param ids: real ids where search
        :param day: date to search
        :return: True or False

        '''
        day = datetime_user_to_server_tz(self._cr, self._uid, normalize_dt(day),
                                         self._context.get('tz'))
        day_str = normalize_dt_str(day.replace(hour=23, minute=59))
        res_ids = self.search([('id', 'in', self._ids), ('date', '<=', day_str)])
        for data in res_ids.read(['date', 'calendar_duration']):
            d_from = normalize_dt(data['date'])
            d_to = d_from + timedelta(hours=data.get('calendar_duration'))
            if d_from.date() <= day.date() <= d_to.date():
                return True
        return False

    @api.model
    @api.returns('self', downgrade=_SEARCH_DOWNGRADE)
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """If 'virtual_id' not in context or are False then normally
        search, else search virtual occurrences and return then.

        """
        _super = super(RecurrentModel, self).search
        res = _super(args, offset=offset, limit=limit, order=order, count=False)
        if not res:
            return self.browse()
        if self._context.get('virtual_id', True):
            res = self.browse(res._get_virtuals_ids(args, offset, limit))
        if limit:
            res = res[offset:offset + limit]
        if count:
            return len(res)
        return res

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        '''Return the list of dict with the [fields].
        if [ids] contain virtual ids read data from real ids and create
        virtual copies to return

        If :param fields: have [date, date_from, date_to] return a list of dict
        with this fields plus id. If :param calendar_duration: is include in
        fields it will be add to the result else is exclude.
        '''
        _super = super(RecurrentModel, self).read
        if not self._context.get('virtual_id', True):
            return _super(fields, load=load)
        if not fields:
            fields = []
        fields2 = fields[:] if fields else []
        targets = ('date', 'date_from', 'date_to')
        has_dates = any(field in fields for field in targets)
        if fields and 'calendar_duration' not in fields and has_dates:
            fields2.append('calendar_duration')
        ids_index = {record.id: int(self._virtual_id2real(record.id))
                     for record in self}
        # If dict:ids_index have as keys virtual_ids:(str,unicode) the
        # id_reals are dict.values() else the id_reals are dict.keys()
        keys = ids_index.keys()
        if keys:
            if isinstance(keys[0], (str, unicode)):
                real_ids = self.browse(ids_index.values())
            elif keys and isinstance(keys[0], int):
                real_ids = self.browse(keys)
        else:
            real_ids = self.browse()
        real_data = super(RecurrentModel, real_ids.with_context(
            virtual_id=False)).read(fields2)
        real_data = {row['id']: row for row in real_data}
        result = []
        for virtual_id, real_id in ids_index.items():
            res = real_data.get(real_id, {}).copy()
            # If :param fields have (date,date_from or date_to)
            if has_dates:
                ls = self._virtual_id2real(virtual_id,
                                           with_date=res.get(
                                               'calendar_duration') or 23)
                # ls is a tuple E.g. (id, date_start,date_end)
                if is_collection(ls) and len(ls) >= 2:
                    if res.get('date_from'):
                        res['date_from'] = normalize_d_str(ls[1])
                    if res.get('date'):
                        res['date'] = normalize_dt_str(ls[1])
                    if res.get('date_to'):
                        res['date_to'] = normalize_d_str(ls[2])
            res['id'] = virtual_id
            result.append(res)
        # If calendar_duration not is in :param fields:,it's remove of result.
        if fields and 'calendar_duration' not in fields:
            for r in result:
                r.pop('calendar_duration', None)
        if not self._ids:
            return result[0] if result else []
        return result

    @api.multi
    def unlink(self):
        # TODO: implement the logic for rule exceptions and one occurrence
        # modifications.
        self._check_for_one_occurrency_change()
        return super(RecurrentModel, self).unlink()

    @api.multi
    def write(self, values):
        # TODO: implement the logic for rule exceptions and one occurrence
        # modifications.
        self._check_for_one_occurrency_change()
        res = super(RecurrentModel, self).write(values)
        if 'no_update_rrule' not in self._context and not values.get('rrule'):
            self._update_rrule()
        return res

    @api.model
    def create(self, values):
        recurrence = super(RecurrentModel, self).create(values)
        if recurrence:
            recurrence._update_rrule()
        return recurrence

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
