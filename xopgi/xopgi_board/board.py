# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xopgi_board.board
# ---------------------------------------------------------------------
# Copyright (c) 2014, 2015 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2015-10-29

from openerp import api, models
from itertools import groupby


def lineal_color_scaling(value,  # 0-1 float
                         start_point=(255, 0, 0),  # red
                         end_point=(0, 255, 0)):  # green
    from colorsys import rgb_to_hsv, hsv_to_rgb as _hsv_to_rgb
    start_point = rgb_to_hsv(*start_point)
    end_point = rgb_to_hsv(*end_point)

    def hsv_to_rgb(*a):
        res = _hsv_to_rgb(*a)
        return tuple(int(x) for x in res)

    def transition(value, start_point, end_point):
        return start_point + (end_point - start_point) * value

    def transition3(value, (s1, s2, s3), (e1, e2, e3)):
        r1 = transition(value, s1, e1)
        r2 = transition(value, s2, e2)
        r3 = transition(value, s3, e3)
        return (r1, r2, r3)

    return hsv_to_rgb(*transition3(value, start_point, end_point))


class XopgiBoard(models.Model):
    _name = 'xopgi.board'
    _description = "Board"

    @api.model
    def get_board_widgets(self):
        lst = self.get_data()
        result = [list(itr) for k, itr in
                  groupby(lst, lambda x: x.get('category', x) or x)]
        return result

    def get_data(self):
        return self.env['xopgi.board.widget'].get_widgets_dict()

    @api.model
    def modify_target_dashboard(self, target_name, target_value,
                                mode='individual'):
        target_obj = (self.env.user.company_id.sudo()
                      if mode == 'company'
                      else self.env.user.sudo())
        target_value = int(target_value) if target_value else 0
        if hasattr(target_obj, 'target_' + target_name):
            return setattr(target_obj, 'target_' + target_name, target_value)
