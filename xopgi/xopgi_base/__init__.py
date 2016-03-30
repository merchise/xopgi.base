# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi.addons.xopgi_base.__init__
# ---------------------------------------------------------------------
# Copyright (c) 2013-2015 Merchise Autrement
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# @created: 2013-04-09

'''
==========
XOPGI Base
==========

Correct some usability and functional scenarios of `OpenERP` Base models.


res.partner
===========

This model has multiple attributes which corresponds with external concepts
(partner delegates).

Delegates are entities, all with the same identity and represented by an unique
`res.partner` instance.

There are two ways to become a delegate:

* Inheriting by delegation (directly or not) from `res.partner`

* Through a many2one relationship with `res.partner`


A new model (partner.identity) must be created in order to formalize all the
cases, preliminary will be configured:

* "res.users": through direct inheritance ("partner_id" field)

* "res.company": through direct relationship ("partner_id" field)

* "res.customer": will be a new model with a many2one relationship through
                  "partner_id" field.
                  New models similar to this could be created to manage
                  concepts of this type (suppliers, prestataires, brokers,
                  associations, etc.).
                  Another way to create this concepts is through a simple
                  "semantic classification" in a node defined as "domain"
                  (see below).
                  This kind of models will be defined in related addons, for
                  example: "xopgi_sale", "xopgi_purchase".

* "res.supplier": will be a new model with a many2one relationship through
                  "partner_id" field.

* "hr.employee": inherits from "resource.resource" ("resource_id" field), and
                 then through indirect relationship ("user_id" field).
                 In this case identity is optional; if the employee has the
                 relationship, then is identified by the partner, otherwise
                 it hasn't identity.
                 This case will be implemented in "xopgi_hr" module.


Semantic Classification
=======================

Semantic Classification must be done through a pattern using a mixin named
"ir.kos_mixin" (python inheriting from "osv.orm.AbstractModel").

This pattern define the following attributes:

* is_domain: Expressing that a node with this attribute in True can't be used
             as a direct classificator.

* rule_ids: Rules than must be executed when a classification node is applied
            to an object.
            This kind of rules must be also generalized for the "identity"
            pattern.


Using this pattern, the model "res.partner.category" will be extended and then
will be some standard classifiers (with "is_domain" in True) that will imply
concepts similar to "res.customer".


Usability Scenarios
===================

All former concepts must be applied to all views and menus as correspond.

For example, when we create the concept implied in "res.customer", all
attributes that logically belongs to it, must disappears from all forms and
menus where the "res.partner" doesn't represent a customer.

Also, is some contexts (several employees identified by a unique partner) must
be showed only once with internal list of each concrete object.

'''

from __future__ import absolute_import

from openerp.release import version_info as ODOO_VERSION_INFO

if ODOO_VERSION_INFO < (9, 0):
    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.

    from . import res_users  # noqa
