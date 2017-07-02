xopgi_recurrence (Recurrent Model)
==================================
Model for recurrent things (in time).

It's very similar of recurrence in the calendar module, with some adjustments.

``recurrent.model`` defines fields use to define the conditions in a timeline
and the recurrence rules (to see module :mod:`dateutil.rrule`) in which a given
activity can occur.

You can declare a recurrence in a time interval -'Repeat every' for example:
Recurrent pattern
Repeat every: 1  (Days/Week/Month/Year) any event.

You can also state how often, days of the week, days of the month or at
what time of year the recurrence may occur.
