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


# TODO: xoutil, xoeuf.  TODO: migrate
class Predicate(object):
    '''A predicate to match a `domain`.

    Instances are callables that take a single recordset and test if it
    matches the domain.

    .. warning:: We don't support queries that require traversing a relation.
       This entails we don't support domains using 'child_of'.

    '''
    def __init__(self, domain):
        self.source = source = build_predicate(tuple(domain))
        code = compile(
            source,
            '<predicate for domain {!r}>'.format(domain),
            'eval'
        )
        self.func = eval(code, {}, {})

    def __call__(self, record):
        return self.func(record)

    def __repr__(self):
        return self.source


def build_predicate(domain):
    'Actual implementation of Predicate.'
    from xoeuf.osv.expression import (
        NOT_OPERATOR,
        AND_OPERATOR,
        TRUE_LEAF,
        FALSE_LEAF
    )
    # The operators exists as operators in Python
    BASIC_OPERATORS = ['=', '!=', '<=', '<', '>', '>=', 'in', 'not in', '=?']

    def translate_term(term):
        if term == TRUE_LEAF:
            return 'True'
        elif term == FALSE_LEAF:
            return 'False'
        # else:
        attr, operator, value = term
        if operator not in BASIC_OPERATORS:
            # We don't support child_of
            assert operator in ('like', 'ilike', 'not like', 'not ilike',
                                '=like', '=ilike')
            if operator == 'like':
                return '{value!r} in self.{attr}'.format(value=value, attr=attr)
            elif operator == 'ilike':
                return '{value!r}.lower() in self.{attr}.lower()'.format(value=value, attr=attr)
            elif operator == 'not like':
                return '{value!r} not in self.{attr}'.format(value=value, attr=attr)
            elif operator == 'not ilike':
                return '{value!r}.lower() not in self.{attr}.lower()'.format(value=value, attr=attr)
            elif operator == '=like':
                return '{value!r} == self.{attr}'.format(value=value, attr=attr)
            elif operator == '=ilike':
                return '{value!r}.lower() == self.{attr}.lower()'.format(value=value, attr=attr)
        else:
            if operator in ('=', '=?'):
                operator = '=='
            return 'self.{attr} {operator} {value!r}'.format(
                attr=attr,
                operator=operator,
                value=value
            )

    def translate_operator(op, args):
        if op == NOT_OPERATOR:
            return 'not ({})'.format(args[0])
        else:
            left, right = args
            operator = 'and' if op == AND_OPERATOR else 'or'
            return '({}) {} ({})'.format(left, operator, right)

    def translate(what, stack):
        type_, payload = what
        if type_ == 'TERM':
            stack.append(translate_term(payload))
        else:
            if payload == NOT_OPERATOR:
                # The only unary operator, all others take exactly two items
                args = (stack.pop(-1), )
            else:
                args = (stack.pop(-1), stack.pop(-1))
            stack.append(translate_operator(payload, args))

    stack = []
    for node in walk_domain(domain):
        translate(node, stack)
    assert len(stack) == 1, stack
    return 'lambda self: bool({})'.format(stack.pop(-1))


# xoeuf.osv.expression.DomainTree will gain a powerful `walk` method.  We
# can't use it however due to bugs in DomainTree.
def walk_domain(domain):
    '''Performs a post-fix walk of the 2nd normal form of `domain`.

    Yields tuples of ``(kind, what)``.  `kind` can be either 'TERM' or
    'OPERATOR'.  `what` will be the term or operator.  For `term` it will the
    tuple ``(field, operator, arg)`` in Odoo domains.  For `operator` it will
    be the string identifying the operator:

      >>> d = [('a', '=', 1), ('b', '=', 2), ('c', '=', 3)]
      >>> list(walk_domain(d))
      [('TERM', ('a', '=', 1)),
       ('TERM', ('c', '=', 3)),
       ('OPERATOR', '&'),
       ('TERM', ('b', '=', 2)),
       ('OPERATOR', '&')]

    Notice we emit operators as soon as all its operands have been emitted:

      >>> d = [('a', '=', 1), '|', ('b', '=', 2), ('c', '=', 3)]
      >>> list(walk_domain(d))
      [('TERM', ('a', '=', 1)),
       ('TERM', ('b', '=', 2)),
       ('TERM', ('c', '=', 3)),
       ('OPERATOR', '|'),
       ('OPERATOR', '&')]


    '''
    from xoeuf.osv.expression import (
        Domain,
        NOT_OPERATOR,
        OR_OPERATOR,
        AND_OPERATOR
    )
    BINARY_OPERATORS = [OR_OPERATOR, AND_OPERATOR]
    OPERATORS = BINARY_OPERATORS + [NOT_OPERATOR]
    domain = Domain(domain).second_normal_form
    stack = []

    def maybe_pop_stack():
        popping = True
        while stack and popping:
            operator, arity = stack[-1]
            arity -= 1
            stack[-1] = (operator, arity)
            if arity == 0:
                stack.pop(-1)
                yield ('OPERATOR', operator)
            else:
                popping = False

    for item in domain:
        if item in OPERATORS:
            # For each operator, we put the `(operator, arity)` in the top of
            # the stack, each time we yield a term we substract from the top
            # `arity`, when it reaches zero, we pop the stack.
            if item in BINARY_OPERATORS:
                top = (item, 2)
            else:
                top = (item, 1)
            stack.append(top)
        else:
            yield ('TERM', item)
            for operators in maybe_pop_stack():
                yield operators

    assert not stack, stack
