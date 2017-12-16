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

import operator
from operator import itemgetter

from dateutil import rrule
from datetime import datetime, timedelta

from six import string_types

from xoeuf import api, models, fields
from xoeuf.odoo import _
from xoeuf.odoo.exceptions import ValidationError
from xoeuf.osv import datetime_user_to_server_tz
from xoeuf.tools import normalize_datetime as normalize_dt
from xoeuf.tools import normalize_date
from xoeuf.tools import normalize_datetimestr as normalize_dt_str
from xoeuf.tools import normalize_datestr as normalize_d_str

from .describe import RECURRENT_DESCRIPTION_MODEL


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


_HOURS_PER_DAY = 24
_SECS_PER_HOUR = 3600
_V_DATE_FORMAT = "%Y%m%dT%H%M%S"


def _required_field(field='A field'):
    raise ValidationError(field + _(' is required.'))


#: The model name of the recurrent mixin defined below.
RECURRENT_MIXIN_MODEL = 'recurrent.model'


class RecurrentModel(models.AbstractModel):
    '''A mixin for recurrent things (in time).

    This mixin modifies `search` so that your model can be seen as an
    occurrence of the recurrent event.  You must provide `search_occurrences`
    (or the deprecated `virtual_id`) context key to True to trigger this
    behavior.

    The actual recurrence model is that implemented by the python module
    `dateutil.rrule`:mod:.

    Examples::

      class MyMeeting(Model):
          _name = 'my.meeting'
          _inherit = [_name, 'recurrent.model']

      >>> Meeting = self.env['my.meeting']

      # Case 1:Repeat once every day

      >>> meeting = Meeting.create(dict(
      ...    interval=1,
      ...    freq='daily',
      ...    end_type='no_end_date'
      ... ))

      # Case 2:Repeat each week on Mondays and Fridays

      >>> meeting = Meeting.create(dict(
      ...    interval=1,
      ...    freq='weekly',
      ...    mo=True,
      ...    fr=True,
      ...    end_type='no_end_date'
      ... ))

      # Case 3:Repeat each month the nth days Mondays and Fridays':

      >>> meeting = Meeting.create(dict(
      ...    interval=1,
      ...    freq='monthly',
      ...    days_option='week_day',
      ...    mo=True,
      ...    fr=True,
      ...    end_type='no_end_date'
      ... ))


      # Case 4:Repeat each month the cardinal days of month:

      >>> meeting = Meeting.create(dict(
      ...    interval=1,
      ...    freq='monthly',
      ...    days_option='month_day',
      ...    monthly_day=5,
      ...    end_type='no_end_date',
      ...    end_type='no_end_date'
      ... ))

      # Repeat each year, similar to case three specifying that month of the
      # year.

      >>> meeting = Meeting.create(dict(
      ...    interval=1,
      ...    freq='yearly',
      ...    days_option='month_day',
      ...    monthly_day=5,
      ...    months=1,
      ...    end_type='no_end_date'
      ... ))

      # Repeat each year specifying number of days before western easter
      # sunday.

      >>> meeting = Meeting.create(dict(
      ...    interval=1,
      ...    freq='yearly',
      ...    is_easterly=True,
      ...    byeaster_day=-2,
      ...    end_type='no_end_date'
      ... ))

    :attr months: specify year month.
    :attr monthly_day: Refers to the nth day of the month.
    :attr byeaster: Number of days from western easter sunday by default is 0.

    '''
    _name = RECURRENT_MIXIN_MODEL
    _inherit = [RECURRENT_DESCRIPTION_MODEL]
    _description = 'Recurrent model'

    date_to = fields.Date(
        'Final date',
        help='End date of the occurrence'
    )


    @api.multi
    def _get_date(self):
        '''Get the values for the compute 'date' field of the recurrent object
        using the user timezone.  This is calculated with the field 'date_from'.

        '''
        for item in self:
            # Plus an hour to avoid the problem with daylight saving time.
            date_from = normalize_dt(item.date_from) + timedelta(hours=1)
            if isinstance(item.id, string_types):
                start, _ = self._extract_dates(item.id,
                                               item.calendar_duration or 23)
                item.date = normalize_dt_str(start)
            else:
                item.date = normalize_dt_str(date_from)

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

    date = fields.Datetime(
        compute=_get_date,
        search=_search_date,
        method=True,
        string='Date and time for representation in calendar views',
    )

    calendar_duration = fields.Float(
        compute='_get_duration',
        method=True,
        string='Duration',
        help='Get the duration on hours of the recurrence'
    )

    active = fields.Boolean(
        'Active',
        default=True,
        help='Indicate if recurrent object is active or not'
    )

    is_recurrent = fields.Boolean(
        'Is recurrent',
        default=True,
        help='Check if is recurrent.'
    )

    @staticmethod
    def parse_until_date(until):
        '''Set of 11PM hour of day on UTC

        '''
        end_date_new = normalize_dt(until).replace(hour=23)
        return end_date_new.strftime(_V_DATE_FORMAT)

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

    @api.requires_singleton
    def _iter_ocurrences(self, start=None):
        '''Yields all occurrences of `self` since `start`.

        If `start` is None we start at the earliest possible date.

        Each item is a dictionary with keys `date`, `duration` and `id`
        (virtual id).

        Notice that this generator is possible infinite.  So you should use in
        a procedure that filters and or limits it.

        '''
        from xoutil.eight import integer_types
        if not isinstance(self.id, integer_types) or not self.is_recurrent:
            raise TypeError('_iter_ocurrences requires a recurrent object', self)
        if start is None:
            start = self.date_from

        # We hide the generator so that requirements (TypeError above) are
        # checked at call-time and not at iteration-time.
        def _generator(self, start):
            for date in self.iter_from(start):
                yield dict(
                    id=self._get_occurrence_id(date),
                    date=date,
                    duration=self.calendar_duration,
                )

        return _generator(self, start)

    @api.requires_singleton
    def _get_occurrence_id(self, dt):
        'Return the virtual id a single occurrence at the given datetime `dt`.'
        from xoeuf.tools import normalize_datetimestr
        return '{}-{}'.format(self.id, normalize_datetimestr(dt))

    @api.multi
    def _iter_occurrences_dates(self, start=None):
        '''Produce **all** the occurrences.

        Each item is pair of `(date, record)`, where `date` is the date of an
        occurrence defined by `record.  Records are all the records in `self`.

        Items are produced from `start` to end in order of occurrence.  Thus,
        items from different records can be intertwined.

        If `start` is None, use the first possible date (`date_from`) for all
        items.

        If any record in `self` is not recurrent it will yield a single
        instance with `date` to `date_from`.

        .. note:: This can be a potentially infinite iterator.

        '''
        from xoutil.future.itertools import merge

        def _iter_from(record):
            if record.is_recurrent:
                for date in record.iter_from(start=start):
                    #  The date comes first so that `merge` result be sorted by
                    #  date.
                    yield date, record
            else:
                yield normalize_dt(record.date_from), record

        return merge(*(_iter_from(record) for record in self))

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
                # FIXME: there's no method _get_rulestring.  There's one in
                # model 'calendar.calendar'.
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

    @api.model
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

    @api.model
    def _virtual_id2real(self, virtual_id=None):
        ''' Convert a "virtual id" (type string) into a real id (type int).

        E.g. virtual/recurring event id is 4-20091201100000, so
        it will return 4.

        @param with_date: if a value is passed to this param it will
        return dates based on value of withdate + base_calendar_id

        @return: real id or real id, date

        '''
        from xoutil.eight import string_types
        if virtual_id and isinstance(virtual_id, string_types):
            res = virtual_id.split('-', 1)
            if len(res) >= 2:
                real_id = res[0]
                return real_id
        return virtual_id

    @api.model
    def _extract_dates(self, virtual_id, duration):
        _, res = virtual_id.split('-', 1)
        start = datetime.strptime(res, _V_DATE_FORMAT)
        end = start + timedelta(hours=duration)
        start = normalize_dt_str(start)
        end = normalize_dt_str(end)
        return start, end

    @api.multi
    def _update_rrule(self):
        '''Allow to call the calculation the string representing a rule:
        'rrule' and update the value by each recurrent model.

        '''
        for record in self:
            record.rrule = str(record.get_rrule_from_description())

    @api.model
    def _check_for_one_occurrency_change(self):
        'Ensure only real ids.'
        real_ids = [self._virtual_id2real(x) for x in self.ids]
        if real_ids != self.ids:
            raise ValidationError('Expected only real ids')

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
        virtual_id = self._context.get('virtual_id', False)
        if virtual_id:
            return self._logical_search(args, offset=offset, limit=limit, order=order, count=False)
        else:
            return self._real_search(args, offset=offset, limit=limit, order=order, count=False)

    @api.model
    def _real_search(self, args, offset=0, limit=None, order=None, count=False):
        return super(RecurrentModel, self).search(args, offset=offset, limit=limit, order=order, count=False)

    @api.model
    def _logical_search(self, args, offset=0, limit=None, order=None, count=False):
        res = self._real_search([], offset=offset, limit=limit, order=order,
                                count=False)
        result = [recu._get_virtuals_ids(args, offset, limit) for recu in res]

        virtuals = []
        while(len(result) != 0):
            for virtual in result:
                if len(virtual) == 0:
                    result.remove(virtual)
                if len(virtual) > 0:
                    virtuals.append(virtual.pop(0))
        if virtuals:
            result = self.browse(virtuals)
        else:
            return self.browse()
        if limit:
            result = result[offset:offset + limit]
        if count:
            return len(result)
        return result

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        '''Return the list of dict with the [fields].
        if [ids] contain virtual ids read data from real ids and create
        virtual copies to return

        If :param fields: have [date, date_from, date_to] return a list of dict
        with this fields plus id. If :param calendar_duration: is include in
        fields it will be add to the result else is exclude.
        '''
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
        ids_reals = list(set(ids_index.values()))
        reals = self.browse(ids_reals)
        values = super(RecurrentModel, reals).read(fields2, load=load)
        results = {r['id']: r for r in values}

        def select(virtual_id, data):
            if data is None:
                return None
            else:
                if isinstance(virtual_id, string_types):
                    date_show, _ = self._extract_dates(virtual_id, 23)
                    data['id'] = virtual_id
                    data['date'] = date_show
                return data

        return list(filter(bool, (
            select(key, results.get(ids_index[key], None))
            for key in ids_index
        )))

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
