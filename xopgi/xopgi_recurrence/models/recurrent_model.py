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

from datetime import datetime, timedelta

from six import string_types

from xoeuf import api, models, fields
from xoeuf.odoo import _
from xoeuf.odoo.exceptions import ValidationError
from xoeuf.osv import datetime_user_to_server_tz
from xoeuf.tools import normalize_datetime as normalize_dt
from xoeuf.tools import normalize_date
from xoeuf.tools import normalize_datetimestr as normalize_dt_str

from .describe import RECURRENT_DESCRIPTION_MODEL


def _SEARCH_DOWNGRADE(self, value, args, offset=0, limit=None, order=None,
                      count=False):
    return list(value.ids) if not count else value


_HOURS_PER_DAY = 24
_SECS_PER_HOUR = 3600
_V_DATE_FORMAT = "%Y%m%dT%H%M%S"


def _required_field(field='A field'):
    raise ValidationError(field + _(' is required.'))


#: The model name of the recurrent mixin defined below.
RECURRENT_MIXIN_MODEL = 'recurrent.model'


#: The maximal amount of occurrences to return in a logical (occurrence-based)
#: search.
MAX_OCCURRENCES = 1000


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

    @api.model
    @api.returns('self', downgrade=_SEARCH_DOWNGRADE)
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """If 'virtual_id' not in context or are False then normally
        search, else search virtual occurrences and return then.

        """
        virtual_id = self._context.get('virtual_id', False)
        if virtual_id and not count:
            return self._logical_search(args, offset=offset, limit=limit, order=order)
        else:
            return self._real_search(args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def _real_search(self, args, offset=0, limit=None, order=None, count=False):
        return super(RecurrentModel, self).search(
            args,
            offset=offset,
            limit=limit,
            order=order,
            count=count
        )

    @api.model
    def _logical_search(self, domain, offset=0, limit=None, order=None):
        '''Finds all occurrences that match the domain.

        Since there can be an unlimited number of occurrences, `limit` is
        always bounded to MAX_OCCURRENCES.

        '''
        import operator
        from xoutil.future.functools import reduce
        from xoutil.future.itertools import ifilter, first_n, map
        from xoutil.eight import integer_types
        from xoutil.fp.tools import compose
        from ..tools.predicate import Predicate

        # Normalize limit to be 0 <= limit <= MAX_OCCURRENCES.  If limit is
        # zero, bail the whole procedure by returning the empty recordset
        limit = min(max(limit or 0, 0), MAX_OCCURRENCES)
        if not limit:
            return self.browse()

        # This is a tricky implementation to get right.  Domain can be
        # arbitrarily complex, and mix date-related and non-date related
        # conditions.  Since all non-date related conditions will match for
        # both the occurrences and the recurrent pattern itself, we'd like to
        # find the *recurrence patterns* that match the domain **striping the
        # date-related conditions**, and then rematch the occurrences with the
        # rest of the date-related domain.
        #
        # This is to say that if we're given a domain T that may contain
        # date-related conditions, we would like to find another domain Q
        # without date-related conditions such that ``T => Q``.
        #
        # Then we could find recurrence patterns that match Q, and afterwards
        # filter occurrences by T.  This would make the amount of filtering
        # done in Python less of an issue.
        #
        # Trivially, for any T, making ``Q=[]`` (i.e always True) satisfies
        # this condition, but then will have to filter all of the recurrence
        # in Python and that might be a performance issue.
        #
        # Yet, trying to find a non-trivial Q cannot be achieved in all cases.
        #
        # In the following, all capitalized symbols starting with D will
        # represent predicates (terms in a domain) involving the `date` field,
        # non capitalized symbols will represent predicates not involving the
        # `date` field.  The logical AND and OR will be represented by `and`
        # and `or`, where the logical NOT will be `~`.
        #
        # For the predicate T ``(D or ~n) and (~D or n)``, Q can be ``~n or
        # n``, with is the same as ``[]``.  For the predicate ``(D or n) and
        # (~D or n)``, we can find Q as ``n``.  Notice that both predicates
        # are in Conjunctive Normal Form (CNF).
        #
        # For Odoo domains, we can use the 2nd normal form (2NF) which
        # distributes NOT within the term themselves, this mean we won't see
        # any ``~`` in our predicates.  So a CNF can be ``(D or nn) and (DD or
        # n)`` that will yield Q to be ``~nn or ~n``, which *we* (but not our
        # machinery) know to be equivalent to ``[]``.
        #
        # If the domain is given in CNF and 2NF, it's easy to find Q. So, the
        # algorithm needed is to find the CNF for the 2NF of a domain.
        #
        # HOWEVER, I believe that this is NOT currently needed IN OUR CASE.
        # So let's mark it as a thing to do.
        #
        # TODO:  Compute the CNF to get Q.
        #
        res = self._real_search([], order=order)
        # At this point `res` has the recurrence in the order requested.
        # _iter_occurrence will yield the occurrences in the `date` order
        # first.
        assert all(isinstance(r.id, integer_types) for r in res)
        pred = Predicate(domain)
        occurrences = first_n(ifilter(pred, map(
            compose(self.browse, self._real_id2virtual),
            res._iter_occurrences_dates()
        )), limit)
        return reduce(operator.or_, occurrences, self.browse())

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

    @api.multi
    def _iter_occurrences_dates(self, start=None):
        '''Produce **all** the occurrences.

        Each item is pair of `(date, record)`, where `date` is the date of an
        occurrence defined by `record.  Records are all the records in
        `self`.  `date` is always a `datetime`:class: object.

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

    @api.model
    def _real_id2virtual(self, recurrent_date, real_id):
        if real_id and recurrent_date:
            recurrent_date = normalize_dt(recurrent_date)
            recurrent_date = recurrent_date.strftime(_V_DATE_FORMAT)
            return '%d-%s' % (real_id, recurrent_date)
        return real_id

    @api.model
    def _virtual_id2real(self, virtual_id=None):
        from xoutil.eight import string_types
        if virtual_id and isinstance(virtual_id, string_types):
            res = virtual_id.split('-', 1)
            if len(res) >= 2:
                real_id = res[0]
                return real_id
        return virtual_id

    @api.model
    def _extract_dates(self, virtual_id, duration):
        '''Extract start and end dates from the virtual id and duration.'''
        _, res = virtual_id.split('-', 1)
        start = datetime.strptime(res, _V_DATE_FORMAT)
        end = start + timedelta(hours=duration)
        start = normalize_dt_str(start)
        end = normalize_dt_str(end)
        return start, end

    @api.multi
    def _update_rrule(self):
        '''Update the rrule string representation.'''
        for record in self:
            record.rrule = str(record.get_rrule_from_description())

    @api.model
    def _check_for_one_occurrency_change(self):
        'Ensure only real ids.'
        real_ids = {self._virtual_id2real(x) for x in self.ids}
        if real_ids != set(self.ids):
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
