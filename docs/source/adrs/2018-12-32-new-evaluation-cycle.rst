========================================
 ADR 2018-12-23.  New evaluation cycle.
========================================

.. contents::


Context
=======

Currently, the CDR agent simply creates an instance of 'cdr.evaluation.cycle';
which automatically selects the events to be checked.  Each event may,
ultimately, entail the evaluation of several control variables.  The entire
process happens within the context of a single Celery Task.

This creates several problems:

- An error in the evaluation of a single variable or evidence stops the entire
  process.   We're seeing several instances of this issue in the Sentry.

- If too many events are evaluated, a time limit can be issued which prevents
  the entire process from succeeding.


Decision
========

Try the approach discussed in `Computing variables only once`_; which, in
summary, requires to compute each variable only-once in it's own job but
allows evidences and events to be update several times.

As for trying avoiding running more than once CDR cycle concurrently we defer
true analysis for another occasion and simply keep the single worker for the
CDR.  The only point here is that jobs to compute variables, evidences and
events cannot have a short expiration time.


Discussion
==========

The problems above can be resolved by evaluating each variable, evidence and
event in its own Celery Job.

This creates the need to perform those jobs in any order respecting the
dependencies.  This suggest doing the evaluation following a topological order
of the dependency graph.

Yet a topological order misses any chance for parallelism: Any variable can be
executed in parallel with other variables.  Furthermore, some variables can be
run in parallel with some evidences and/or events::


    event1             event2             event3          event4
      |                |    |               |               |
      v                |    v               v               |
    evidence1 <--------+  evidence2       evidence3 <-------+
      |   |                |      |           |
      v   +------v v-------+      v           v
    var1        var2              var3       var4


Here, ``var4`` can be executed in parallel with both ``evidence1`` and
``evidence2``; ``var1`` can be executed in parallel with ``evidence2`` but
before ``evidence1``.

Parallelism could make the process terminate faster (depending on available
workers).

Parallelism of CDR jobs
-----------------------

We have used topological sorts before (in the prototype addon).

That algorithm simply scored the nodes of the graph by "depth" of
dependencies.  Applying that algorithm in this graph is not very useful:
variables don't depend from one another; evidences don't depend from one
another, and events don't depend from another.  This means that our algorithm
will assign three scores: 0, for variables; 1, for evidences; and 3 for
events.

Even so, this suggest that some degree of parallelism can be achieved.  Using
the Celery groups and chains; we get the following scheme::

   events = select the events to be evaluated in this cycle
   evidences = find the evidences of events
   variables = find the variables to be evaluated

   from celery import group
   variables_group = group(create_var_job(var) for var in variables)
   evidences_group = group(create_evidence_job(e) for e in evidences)
   events_group = group(create_event_job(ev) for ev in events)
   job = variables_group | evidences_group | events_group
   job(current_evaluation_cycle)

There are two issues with this design:

- Parallelism of the jobs for a single CDR evaluation cycle comes at the
  price of having to avoid running two or more cycles at once.

  We need to keep track of whether an evaluation cycle is running to avoid
  doing work more than needed.

  .. warning:: This issue will come with any design in which the execution
     cycle is spread over several celery jobs.

     So it needs to be solved anyways.

- We don't really mitigate the issue of a rogue variable.  If any variable
  fails, the evidences are not updated and events are not checked.


Mitigating the impact of failures
---------------------------------

The goal of the CRD is to alert.  So it seems reasonable to reduce the amount
of impact of errors in a variable.  An error should only affect the evidences
and events involved.

.. note:: We're also using the CDR to compute indicators shown in the Boards,
          even though the CDR was not designed for that purpose.

The trivial approach
~~~~~~~~~~~~~~~~~~~~

For each event we need to check we create a chain of jobs::

  variables_group | evidence_group | event

The problem with this approach is that shared variables and evidences will
recomputed as many times as needed.

We could try to device some way around this issue.  But let's see if there's
an easy way to avoid issuing the same job twice *for the same cycle*.
Remember, we still have to solve the issue of concurrent cycles.  But having
the same job scheduled more than once for the same cycle is an issue that
emerges with this trivial design.

Computing variables only once
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Our goal is to produce a Celery *program* that:

- Obeys the dependency graph.

- Does not duplicate any computation job.

Our primitives are the callbacks, groups and chains of Celery jobs.

Let's try to produce a program for this graph of evidences and variables::

          e1    e2     e3
          | \  / | \    |
          |  \/  |  \   |
          |  /\  |   \  |
          | /  \ |    \ |
        var 1  var 2  var3


The first jobs are those computing the variables::

  job_var3 = ...
  job_var2 = ...
  job_var1 = ...

Looking at the links between variables and events we notice that each variable
job "notifies" or "enables" one or more evidence jobs.  But that some
evidences need to be notified by several variables.

.. note:: I conducted a little experiment to see if Celery signatures are good
   to keep the jobs running only once::

      @app.task(base=Task, bind=True)
      def variable_job(self, cycle, variable):
          print('Variable job %s in cycle %s' % (variable, cycle))
          if 'doomed' in variable:
              raise RuntimeError('doomed')
          return cycle


      @app.task(base=Task, bind=True)
      def evidence_job(self, cycle, evidence):
          print('Evidence job %s in cycle %s' % (evidence, cycle))
          return cycle


      def create_variable_job(variable, link=None):
          if link is not None:
              return variable_job.s(variable) | link
          else:
              return variable_job.s(variable)


      def create_evidence_job(evidence, link=None):
          if link is not None:
              return evidence_job.s(evidence) | link
          else:
              return evidence_job.s(evidence)

      e1 = create_evidence_job('Evidence 1')
      e2 = create_evidence_job('Evidence 2')
      e3 = create_evidence_job('Evidence 3')
      var3 = create_variable_job('Variable 3', link=group(e2, e3))
      var2 = create_variable_job('Variable 3', link=group(e1, e2))

      group(var2, var3).delay('Cycle 1')

   The log shows that Evidence 2 is run twice::

     Variable job variable 2 in cycle Cycle 1
     Variable job variable 3 in cycle Cycle 1
     Evidence job Evidence 2 in cycle Cycle 1
     Evidence job Evidence 1 in cycle Cycle 1
     Evidence job Evidence 3 in cycle Cycle 1
     Evidence job Evidence 2 in cycle Cycle 1

The problem is that ``e2`` is just a signature of the job.  Whenever I use it,
Celery simply picks the name of the task and arguments an creates a new job.

This demonstrate that we **cannot represent** our run just once network with
the primitives provided by Celery alone.  We would have to make the linking
ourselves.

.. warning:: In order to use GroupResult's ``ready()`` method, I had to change
   the configuration option ``task_ignore_result`` to False in
   ``odoo/jobs.py``.


Now, look at the code of ``variable_job``.  Let's try with a doomed variable::

  Variable job variable 2 in cycle Cycle 1
  Variable job doomed variable 3 in cycle Cycle 1

  Task xopgi.xopgi_cdr.cdr_agent.variable_job[904bb15f-61d4-439b-80a2-728471425083] raised unexpected: RuntimeError('doomed',)
  Traceback (most recent call last):
    File "/home/manu/.buildout/eggs/celery-4.2.0-py2.7.egg/celery/app/trace.py", line 382, in trace_task
      R = retval = fun(*args, **kwargs)
    File "/home/manu/.buildout/eggs/celery-4.2.0-py2.7.egg/celery/app/trace.py", line 641, in __protected_call__
      return self.run(*args, **kwargs)
    File "/home/manu/src/merchise/pgi/xopgi.base/xopgi/xopgi_cdr/cdr_agent.py", line 135, in variable_job
      raise RuntimeError('doomed')
  RuntimeError: doomed

  Evidence job Evidence 2 in cycle Cycle 1
  Evidence job Evidence 1 in cycle Cycle 1

Notice that only the Evidence 3 wasn't fired.  Evidences are idempotent and
run really fast (they only read a variables already computed value) and
perform a simple comparison.

This means that could allow running the same evidence more than once.  Events
can run more than once as well because they only update its "firing"
attribute.


Status
======

Implemented.


Consequences
============

The architecture remains stable.

No unforeseen bad consequences.  In fact, there's a good non-anticipated
consequence: if some variable fails its evidences and events won't be updated
and thus recomputed in the next cycle.


Experimental reports
====================

- Despite what's documented__ about Chords_ needing ``task_ignore_result`` set
  to False; I haven't had the need to do it.

- In some tests, cycles where a task is forcibly terminated (``kill -9`` to
  the worker), the cycle remains in the state ERRORED.  Whereas if the job is
  terminated with a SoftTimeLimitExceeded, the cycle is correctly set to
  DONE_WITH_ERRORS.

  I think we can cope with that.


- I have witnessed two cycles being run at the same time::

    [2018-12-26 16:23:55,822: INFO/ForkPoolWorker-1] Start job (d36e1ced-6636-4cd6-a020-e7a3afa4a53f): db=mercurio, uid=1, model=cdr.control.variable, ids=[23], method=evaluate
    [2018-12-26 16:23:55,823: DEBUG/ForkPoolWorker-1] Multiprocess signaling check: [Registry - 543 -> 543] [Cache - 115449 -> 115449]
    [2018-12-26 16:23:55,845: DEBUG/ForkPoolWorker-1] Start evaluation of [u'partner_rotation_indicator'], cycle: cdr.evaluation.cycle(1253051,)
    [2018-12-26 16:23:55,847: DEBUG/ForkPoolWorker-1] Evaluating u'partner_rotation_indicator'
    [2018-12-26 16:25:39,293: DEBUG/ForkPoolWorker-1] Evaluated u'partner_rotation_indicator'
    [2018-12-26 16:25:39,438: DEBUG/ForkPoolWorker-1] Done computing variable [u'partner_rotation_indicator']
    [2018-12-26 16:25:41,767: INFO/ForkPoolWorker-1] Start job (d110589a-a97b-4aa9-9da6-b3aa97e88e50): db=mercurio, uid=1, model=cdr.agent, ids=[], method=_new_evaluation_cycle
    [2018-12-26 16:25:41,769: DEBUG/ForkPoolWorker-1] Multiprocess signaling check: [Registry - 543 -> 543] [Cache - 115449 -> 115449]
    [2018-12-26 16:25:41,899: INFO/ForkPoolWorker-1] Start job (936990b4-9901-4c2e-ae4b-8c4eb50f6142): db=mercurio, uid=1, model=cdr.evidence, ids=[11], method=evaluate
    [2018-12-26 16:25:41,900: DEBUG/ForkPoolWorker-1] Multiprocess signaling check: [Registry - 543 -> 543] [Cache - 115449 -> 115449]
    [2018-12-26 16:25:43,903: INFO/ForkPoolWorker-1] Start job (1edc161d-9571-4645-9f12-5fc6f35dedda): db=mercurio, uid=1, model=cdr.control.variable, ids=[23], method=evaluate
    [2018-12-26 16:25:43,904: DEBUG/ForkPoolWorker-1] Multiprocess signaling check: [Registry - 543 -> 543] [Cache - 115449 -> 115449]
    [2018-12-26 16:25:43,916: DEBUG/ForkPoolWorker-1] Start evaluation of [u'partner_rotation_indicator'], cycle: cdr.evaluation.cycle(1253052,)
    [2018-12-26 16:25:43,917: DEBUG/ForkPoolWorker-1] Evaluating u'partner_rotation_indicator'

  In psql::

    mercurio=# select * from cdr_evaluation_cycle order by create_date desc limit 10;
       id    | create_uid |        create_date         |         write_date         | write_uid |  state
    ---------+------------+----------------------------+----------------------------+-----------+---------
     1253052 |          1 | 2018-12-26 16:25:41.775158 | 2018-12-26 16:25:41.775158 |         1 | STARTED
     1253051 |          1 | 2018-12-26 16:23:55.732041 | 2018-12-26 16:23:55.732041 |         1 | STARTED
     1253050 |          1 | 2018-12-26 16:19:09.010186 | 2018-12-26 16:21:18.555825 |         1 | ERRORED
     1253049 |          1 | 2018-12-21 03:59:37.673238 | 2018-12-21 03:59:37.673238 |         1 | DONE
     1253048 |          1 | 2018-12-21 03:58:32.41712  | 2018-12-21 03:58:32.41712  |         1 | DONE
     1253047 |          1 | 2018-12-21 03:57:29.341888 | 2018-12-21 03:57:29.341888 |         1 | DONE
     1253046 |          1 | 2018-12-21 03:57:27.482704 | 2018-12-21 03:57:27.482704 |         1 | DONE
     1253045 |          1 | 2018-12-21 03:56:20.560744 | 2018-12-21 03:56:20.560744 |         1 | DONE
     1253044 |          1 | 2018-12-21 03:55:14.993131 | 2018-12-21 03:55:14.993131 |         1 | DONE
     1253043 |          1 | 2018-12-21 03:54:10.418608 | 2018-12-21 03:54:10.418608 |         1 | DONE
    (10 rows)

  I think this is because Celery is trying to make the job (which expires)
  ``_new_evaluation_cycle`` to run before other jobs.  But that's just a guess
  and the order of message delivery is not properly defined.


__ http://docs.celeryproject.org/en/latest/userguide/canvas.html#chord-important-notes

.. _chords: http://docs.celeryproject.org/en/latest/userguide/canvas.html#chords
