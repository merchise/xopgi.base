On actual odoo implementation for dynamic stage models allow non way to
know what stage represent the init or end point of workflow.
E.G. How get all leads that are active (no cancel or won or lose, ...)?

This module provide an abstract model to implement the start and stop flow
values on stage models. The only goal of the module is get the
implementation of that kind of logic on a same place.
E.G above example can be solve with a domain like
`[('stage_id.stop_flow', '=', False)]`

How use
=======

Extend stage model what we want to add this behavior and put it to inherit
from ``base.stage`` and extend it form view to allow edit ``start_flow``
and ``stop_flow`` fields. Then can use that fields on domains.
