#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#

'''User Interface facilities to describe recurrence rules.

This is NOT graphical user interface per se.  But defines the fields we need
to present to a user to help it describe the recurrence.

The main purpose of this module is to translate from human language (fields
and values in a form) to the language of the RFC 2445 (iCal).

'''

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

import datetime
from dateutil import rrule as _rrule

from xoeuf import models, fields, api
from xoeuf.odoo.exceptions import ValidationError

from xoutil.future import calendar


# FIXME: All the following using fields.Enumeration.  Requires a DB migration.

#: The frequency which the events regularly occurs.
FREQ = [
    ('daily', 'Day(s)'),
    ('weekly', 'Week(s)'),
    ('monthly', 'Month(s)'),
    ('yearly', 'Year(s)')
]

DEFAULT_FREQ = 'daily'

DEFAULT_INTERVAL = 1


#: Maps FREQ keys to values for the `dateutil.rrule.rrule`:class: `freq`
#: argument.
FREQ_TO_RULE = {
    key: getattr(_rrule, key.upper()) for key, _ in FREQ
}

#: Recurrence by week day.  This is BYDAY in the RFC 2445.  This is combined
#: with the day of week (MO, TU, ...).  "+2 FR" means the "second Friday",
#: "-1 MO" means the "last Monday".
EVERY_WEEKDAY = 'n'
FIRST_WEEKDAY = '1'
SECOND_WEEKDAY = '2'
THIRD_WEEKDAY = '3'
FOURTH_WEEKDAY = '4'
FIFTH_WEEKDAY = '5'
LAST_WEEKDAY = '-1'
NEXT_TO_LAST_WEEKDAY = '-2'

BYWEEKDAY = [
    (EVERY_WEEKDAY, 'Every'),
    (FIRST_WEEKDAY, 'The First'),
    (SECOND_WEEKDAY, 'The Second'),
    (THIRD_WEEKDAY, 'The Third'),
    (FOURTH_WEEKDAY, 'The Fourth'),
    (FIFTH_WEEKDAY, 'The Fifth'),
    (LAST_WEEKDAY, 'The Last'),
    (NEXT_TO_LAST_WEEKDAY, 'The next to last'),
]

DEFAULT_BYWEEKDAY = EVERY_WEEKDAY


if hasattr(calendar, 'MONTHS'):
    MONTHS = [(str(i + 1), month) for i, month in enumerate(calendar.MONTHS)]
else:
    MONTHS = [
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')
    ]


#: When does the last occurrence happens
NO_END = DOES_NOT_END = DEFAULT_END_TYPE = 'no_end_date'
ENDS_AT = UNTIL = RUNS_UNTIL = 'until'
ENDS_AFTER_MANY = RUNS_FOR = COUNT = 'count'

END_TYPE = [
    (DOES_NOT_END, 'No end date'),
    (UNTIL, 'Until'),
    (COUNT, 'Number of repetitions')
]


#: Which type of recurrence? By day of the week, or day of the month?
USE_WEEK_DAY = 'week_day'
DEFAULT_WEEK_MONTH = USE_MONTH_DAY = 'month_day'

SELECT_WEEKDAY_MONTHDAY = [
    (USE_WEEK_DAY, 'By week day'),
    (USE_MONTH_DAY, 'By month day')
]


class DayOfWeek(models.AbstractModel):
    _name = 'recurrence.abs.day_of_week'

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

    @fields.Property
    def _weekno(self):
        return [
            getattr(_rrule, attr.upper())
            for attr in ('mo', 'tu', 'we', 'th', 'fr', 'sa', 'su')
            if getattr(self, attr)
        ]


RECURRENT_DESCRIPTION_MODEL = 'recurrence.abs.definition'


class RecurrentRuleDefinition(models.AbstractModel):
    '''A recurrence definition mixin.

    The model behind this definition is that of the python module
    `dateutil.rrule`:mod:.

    '''
    _name = RECURRENT_DESCRIPTION_MODEL
    _inherit = ['recurrence.abs.day_of_week']

    date_from = fields.Date(
        'Initial date',
        required=True,
        default=fields.Date.today,
        # XXX: When we return an occurrence this matches the date of the
        # occurrence.
        help='Date at which this recurrent event starts.'
    )

    duration = fields.Integer(
        'Duration',
        default=1,
        help='Duration (days) of each occurrence'
    )

    allday = fields.Boolean(
        'All Day',
        default=True,
        help='Is this a day-long occurrence?',
    )

    freq = fields.Selection(
        FREQ,
        'Frequency type',
        default=DEFAULT_FREQ,
        # XXX: Don't put this, because there's an error in the JS client that
        # messes up with the invisible toggling we have there.
        # help='Frecuency type (Daily/Weekly/Monthly/Yearly)'
    )

    interval = fields.Integer(
        'Repeat Every',
        default=DEFAULT_INTERVAL,
        help='Repeat every ...',
    )

    # Recurrence by month data.
    days_option = fields.Selection(
        SELECT_WEEKDAY_MONTHDAY,
        'Option',
        default=DEFAULT_WEEK_MONTH,
        help='Does this occur on the same day of the month, or the week',
    )

    monthly_day = fields.Integer(
        'Days of month',
        default=lambda *args: datetime.date.today().day
    )

    by_week_day = fields.Selection(
        BYWEEKDAY,
        'Reference',
        default=DEFAULT_BYWEEKDAY,
        help=("Used in combination with each week day selection.  If you "
              "check Monday, then this can mean: every Monday, the first "
              "Monday, the last Monday, etc... You may choose several week "
              "days.")
    )

    months = fields.Selection(
        MONTHS,
        'Month',
        deafault=lambda *args: str(datetime.date.today().month),
        help="The month of the year at which this event reoccurs."
    )

    is_easterly = fields.Boolean(
        'By easter',
        help="For events that reoccurs based on Western Easter Sunday."
    )

    byeaster = fields.Integer(
        'By easter',
        default=0,
        help='Number of days from Western Easter Sunday.'
    )

    # In this model, the end of recurrence is EITHER: a) does not have and
    # end, b) after many instances,  c) after a given date.
    end_type = fields.Selection(
        END_TYPE,
        'Recurrence Termination',
        default=DOES_NOT_END,
        help="How this recurrence stops from happening."
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

    # TODO: Should we need to store this in the DB?
    rrule = fields.Char(
        'RRULE',
        size=124,
        readonly=True,
        default='',
        compute='_compute_rrule_string',
        help=('This field is update after to creates or to update the recurrent'
              ' model by the function  _update_rrule. By default it is taken'
              ' value but then it is calculated and takes a similar value.'
              ' E.g. rrule=FREQ=WEEKLY;INTERVAL=1;BYDAY=TU,MO'),
    )

    @api.depends('count', 'until', 'end_type', 'mo', 'tu', 'we', 'th', 'fr',
                 'sa', 'su', 'is_easterly', 'byeaster', 'months', 'monthly_day',
                 'by_week_day', 'freq', 'days_option', 'interval')
    def _compute_rrule_string(self):
        for record in self:
            record.rrule = str(record.get_rrule_from_description())

    def get_rrule_from_description(self):
        '''The recurrent rule that describes this recurrent event.

        :returns: `dateutil.rrule.rrule`:class:.

        '''
        from xoeuf.tools import normalize_date
        kwargs = dict(
            dtstart=normalize_date(self.date_from),
            interval=max(1, self.interval or 0),
        )
        if self.end_type == ENDS_AT:
            kwargs['until'] = max(normalize_date(self.date_from),
                                  normalize_date(self.until))   # or date_to?
        elif self.end_type == ENDS_AFTER_MANY:
            kwargs['count'] = min(1, self.count)
        else:
            assert self.end_type == DOES_NOT_END
        if self.days_option == USE_WEEK_DAY:
            kwargs['byweekday'] = self.byweekday
        elif self.days_option == USE_MONTH_DAY:
            kwargs['bymonthday'] = self.monthly_day
        else:
            assert False
        if self.is_easterly:
            kwargs['byeaster'] = self.byeaster
        else:
            kwargs['bymonth'] = int(self.months)
        return _rrule.rrule(FREQ_TO_RULE[self.freq], **kwargs)

    @fields.Property
    def byweekday(self):
        return self._weekno

    @api.constrains('monthly_day')
    def _check_monthly_day_no_longer_than_month(self):
        for record in self:
            if not (-31 <= record.monthly_day <= 31):
                raise ValidationError(
                    'You must provide a valid day of the month'
                )

    @api.constrains('byeaster', 'is_easterly')
    def _check_byeaster_no_longer_than_year(self):
        for record in self:
            if record.is_easterly:
                if not (-365 <= record.byeaster <= 365):
                    raise ValidationError(
                        'By Easter must not extend longer than a year'
                    )
