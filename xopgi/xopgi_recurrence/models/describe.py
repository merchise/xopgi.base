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
from xoeuf import models, fields
from xoutil.future import calendar


# FIXME: All the following using fields.Enumeration.  Requires a DB migration.

#: The frequency which the events regularly occurs.
FREQ = [
    ('daily', 'Day(s)'),
    ('weekly', 'Week(s)'),
    ('monthly', 'Month(s)'),
    ('yearly', 'Year(s)')
]

#: Recurrence by week day.  This is BYDAY in the RFC 2445.  This is combined
#: with the day of week (MO, TU, ...).  "+2 FR" means the "second Friday",
#: "-1 MO" means the "last Monday".
BYWEEKDAY = [
    ('n', 'Every'),
    ('1', 'The First'),
    ('2', 'The Second'),
    ('3', 'The Third'),
    ('4', 'The Fourth'),
    ('5', 'The Fifth'),
    ('-1', 'The Last')
    ('-2', 'The next to last')
]


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
END_TYPE = [
    ('no_end_date', 'No end date'),
    ('until', 'Until'),
    ('count', 'Number of repetitions')
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
        from dateutil import rrule
        return [
            getattr(rrule, attr.upper())
            for attr in ('mo', 'tu', 'we', 'th', 'fr', 'sa', 'su')
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
        help='Date to be init of recurrence'
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

    allday = fields.Boolean(
        'All Day',
        default=True
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
        default=lambda *args: datetime.date.today().day
    )

    by_week_day = fields.Selection(
        BYWEEKDAY,
        'Reference',
        default='n',
        help="Selection by week's days E.g.(Every, The First, The Second, The Third,"
             " The Fourth, The Fifth, The Last)"
    )

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

    # In this model, the end of recurrence is EITHER: a) does not have and
    # end, b) after many instances,  c) after a given date.
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
