==================
 A control system
==================

The CDR is a control system.  It allows check the health of the organization
and be responsive to signs of warning.

Overview
========

The entire system is divided in four group of components:

- The `control variables` define basic mostly numeric evaluations of a single
  basic indicator.  For instance, you may define 'the total amount of
  liquidity' you have available.

  Control variables are evaluated when needed.  They hold a single "current"
  value (which is actually the value of the `last evaluation <CDR cycle_>`__),
  and history of past values, which may be discarded at any time.

- The `evidences` are predicates over several `control variables`.  They test
  conditions which are *undesired* regarding those variables.  For example,
  having defined the 'liquidity' and 'current liabilities' variables we may
  defined a 'low liquidity' evidence via the predicate
  ``liquidity < liabilities * 1.1``, which establishes that we need that our
  current cash exceeds the current liabilities by at least 10%.

  In this version, `evidences` are boolean predicates.  We're thinking a
  possible extension to multi-valuate logic like fuzzy sets.

  `Evidences` have a single current value from the last evaluation.  A history
  of values is also available.

- An `event` define *when* should we take action to counteract the causes that
  are constantly triggering an evidence.  In the example above, we may define
  the event 'low liquidity' to trigger after 24 hours of continuously
  witnessing the 'low liquidity' evidence.  We also define here at which pace
  we must evaluate the evidence so that we can react as soon as it's needed.

  Notice the system allows the organization to respond but it does not enforce
  immediate action.  Following the example, your organization may start the
  day doing some purchases that, if evaluated, would set the 'low liquidity'
  evidence to True; but at midday you may receive notification from you bank
  that your account has received a well sized amount from a customer, so the
  'low liquidity' evidence stops being True.  At the end of the day, you're
  quite OK with regards to liquidity; and no event should have triggered.

  How often to check the evidence and how many times, depends on how your
  organization must respond to such event.

  When an event occurs, a `notification` is issued.

- `Notifications` are a broad concept of that what to do in the face of an
  event.


Technical overview
==================

The core concepts are defined in the addon `xopgi_cdr`.  Different types of
notifications are defined in `xopgi_cdr_notification`,
`xopgi_cdr_system_action`.

The addon `xopgi_web_notification` is used to send notifications to the web
client.

The addon `xopgi_recurrence` is used to define a recurrent event.

.. question:: Conceptually all events are recurrent, so why this is a separate
   model?
