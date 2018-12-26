#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright (c) Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can do what the LICENCE file allows you to.
#
from __future__ import division, print_function, absolute_import


def migrate(cr, version=None):
    cr.execute('''
       UPDATE cdr_evaluation_cycle SET state='DONE';
    ''')
