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

import ast

from xoeuf.odoo.tools.safe_eval import safe_eval


def get_free_names(expr):
    '''Detect the names (variable) that are `used free`__ in the 'expr'.

    :param expr: A string representing a Python expression.
    :type expr: string

    :return: A set of names used free in the expression.

    Examples::

        >>> detect_names('all(x for x in this for y in those if p(y)'
        ...              '      for z in y)')
        {'this', 'those', 'p', 'all'}

        >>> detect_names('(lambda x: lambda y: x + y)(x)')
        {'x'}

    .. note:: Builtin names are also reported.  In the first example you may
              see 'all' is the returned set.

    .. note:: Names can be used both free and bound in expressions as
              demonstrated in the second example.

    __ https://en.wikipedia.org/wiki/Free_variables_and_bound_variables

    '''
    tree = ast.parse(expr, '', 'eval')
    detector = NameDetectorVisitor()
    detector.visit(tree.body)  # Go directly to the body
    return detector.freevars


def evaluate(expression, mode='eval', **kwargs):
    '''Evaluate `expression` in the provided `mode`.

    The expression is provided several functions described below.

    If `mode` is 'eval', return the result of the evaluating the expression.

    If `mode` is 'exec', the `expression` SHOULD assign a 'result' variable;
    if it does so, return the value of 'result', otherwise return None.

    Symbols available to `expression`:

    - `xoeuf.tools.date2str`:func:

    - `xoeuf.tools.dt2str`:func:

    - `xoeuf.tools.normalize_datetime`:func:

    - `xoeuf.tools.localize_datetime`:func:

    - `datetime.timedelta`:class:

    - `datetime.datetime`:class:

    - `dateutil.relativedelta.relativedelta`:class:

    '''
    if mode not in ('eval', 'exec'):
        raise ValueError('Invalid value for mode: %r' % mode)
    from xoeuf.tools import date2str, dt2str
    from xoeuf.tools import normalize_datetime, localize_datetime
    from datetime import timedelta, datetime
    from dateutil.relativedelta import relativedelta
    local_dict = kwargs
    local_dict.update(
        date2str=date2str,
        dt2str=dt2str,
        normalize_datetime=normalize_datetime,
        localize_datetime=localize_datetime,
        timedelta=timedelta,
        datetime=datetime,
        relativedelta=relativedelta,
    )
    local_dict.update(globals().get('__builtins__', {}))
    res = safe_eval(expression, local_dict, mode=mode, nocopy=True)
    if mode == 'exec':
        res = local_dict.get('result', None)
    return res


class NameDetectorVisitor(ast.NodeVisitor):
    'Helper class to detect names in a AST.'

    def _with_new_frame(f=None):
        'Helper decorator to maintain a virtual stack frame for names.'
        def method(self, node):
            self.push_stack_frame()
            if f is None:
                self.generic_visit(node)
            else:
                f(self, node)
            self.pop_stack_frame()
        return method

    def __init__(self):
        self.frame = frame = set()
        self.stack = [frame]
        self.freevars = set()

    def push_stack_frame(self):
        self.frame = frame = set()
        self.stack.append(frame)

    def pop_stack_frame(self):
        return self.stack.pop(-1)

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Param)):
            self.bind_variable(node.id)
        elif node.id not in self.bound_variables:
            self.report_free_variable(node.id)
        else:
            self.report_bound_variable(node.id)

    @property
    def bound_variables(self):
        return {name for frame in self.stack for name in frame}

    def bind_variable(self, name):
        self.frame.add(name)

    def report_free_variable(self, name):
        self.freevars.add(name)

    def report_bound_variable(self, name):
        pass

    visit_Lambda = _with_new_frame()

    @_with_new_frame
    def visit_GeneratorExp(self, node):
        # ensure we visit generators first so that we can create the stack
        # frame for variable bindings before they are used in 'elt'.
        for comp in node.generators:
            self.visit(comp)
        self.visit(node.elt)

    visit_SetComp = visit_ListComp = visit_GeneratorExp

    @_with_new_frame
    def visit_DictComp(self, node):
        # almost identical to the method above, but instead of 'elt' there's a
        # 'key' and 'value'.
        for comp in node.comprehesions:
            self.visit(comp)
        self.visit(node.key)
        self.visit(node.value)
