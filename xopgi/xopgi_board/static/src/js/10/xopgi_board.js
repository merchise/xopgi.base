odoo.define('xopgi.base.Board', function (require) {
    'use strict';

    var core = require('web.core');
    var data = require('web.data');
    var form_common = require('web.form_common');
    var Model = require('web.DataModel');
    var pyeval = require('web.pyeval');
    var CalendarView = require('web_calendar.CalendarView');
    var Menu = require('web.Menu');
    var ViewManager = require('web.ViewManager');
    var _t = core._t;
    var QWeb = core.qweb;

    var XopgiBoard = form_common.FormWidget.extend({
        start: function() {
            var self = this;
            return $.when(this._super.apply(this, arguments)).then(function(){
                self.render();
                // Events
                self.$el.delegate('.oe_board_container .oe_fold', 'click',
                                  self.on_fold_action);
                self.$el.delegate('.o_dashboard_action', 'click',
                                  self.on_dashboard_action_clicked);
                self.$el.delegate('.o_target_to_set', 'click',
                                  self.on_dashboard_target_clicked);
            });
        },

        fetch_data: function () {
            var board = new Model('xopgi.board');
            var context = new data.CompoundContext(board.context() || []);
            return board.call('get_board_widgets', [context]);
        },

        render: function () {

            var self = this,
                res = $.Deferred();
            // Get the function to format currencies
            new Model("res.currency")
                .call("get_format_currencies_js_function", ['false'])
                .then(function (data) {
                    self.formatCurrency = new Function("amount, currency_id", data);
                }).then(function () {
                    self.fetch_data().then(function (result) {
                        var dashboard = QWeb.render('xopgi.board', {
                            widget: self,
                            values: result
                        });
                        //Hide panel Preview in Odoo 10
                        $('.o_control_panel.o_breadcrumb_full').hide();
                        $(dashboard).prependTo(self.$el);
                        _.each(result, function (category) {
                            _.each(category, function (values) {
                                if (!!values){
                                    var template_name = '';
                                    if (!!values.template_name) {
                                        template_name = values.template_name;
                                    } else {
                                        template_name = 'no_content';
                                    }
                                    if (!!values.xml_template) {
                                        QWeb.add_template(values.xml_template);
                                    }
                                    var args = values;
                                    args.widget = self;
                                    var template = QWeb.render(template_name, args);
                                    var selector = '.oe_' + template_name.replace('.', '_');
                                    self.$el.find(selector).append(template);
                                }
                            });
                        });
                        self.addGraphs();
                        res.resolve();
                    }, function() {res.reject();});
                });
            return res.promise();
        },

        addGraphs: function () {
            var self = this,
                svgs = self.$el.find('svg');
            _.each(svgs, function (svg) {
                nv.addGraph(function () {
                    return self.get_chart(svg);
                });
            });
        },

        get_chart: function (svg) {
            var self = this,
                $svg = $(svg),
                type = $svg.attr('type'),
                values = $svg.attr('values') || false,
                obj = $svg.attr('obj') || false,
                context = pyeval.eval('context', $svg.data('context'), {}),
                method = $svg.attr('method') || false,
                tmp = $.Deferred();
            if (values) {
                values = JSON.parse(values);
                tmp.resolve();
            }
            else if (!!obj && !!method) {
                new Model(obj)
                    .call(method, [],  {'context': context})
                    .then(function (data) {
                        values = data;
                        tmp.resolve();
                    }, function () {tmp.reject();});
            }
            else {
                tmp.reject();
            }
            return $.when(tmp).done( function () {
                var chart = self.format_graph(type, values);
                d3.select(svg)
                    .datum(values)
                    .transition().duration(500).call(chart);
                nv.utils.windowResize(chart.update);
                return chart;
            });
        },

        format_graph: function(type, values) {
            var self = this;
            var chart;
            switch (type) {
            case 'line':
                chart = nv.models.lineChart();
                chart.yAxis.tickFormat(d3.format(',f'));
                break;
                //TODO: manage other graph type.
            default :
                chart = nv.models.pieChart();
            }
            chart.xAxis.tickFormat(function (d) {
                try {
                    return values[0].values[d].label;
                } catch (err) {
                    return '';
                }
            });
            chart.yAxis.tickFormat(function (d) {
                try {
                    return self.formatCurrency(d, values[0].currency_id);
                } catch (err) {
                    return '';
                }
            });
            chart.options({
                margin: {'left': 100, 'right': 30, 'top': 30, 'bottom': 30},
                showYAxis: true,
                showXAxis: true,
                showLegend: true,
                useInteractiveGuideline: true,
                tooltips: true,
                tooltipContent: function (key, x, y, e, graph) {
                    return self.create_tooltip(x, y, e);
                }
            });
            return chart;
        },

        create_tooltip: function (x, y, e) {
            var title = e.series.key,
                $tooltip = $('<div>').addClass('o_tooltip'),
                value = e.series.currency_id ?
                this.formatCurrency(e.point.y, e.series.currency_id) :
                e.point.y;
            $('<b>')
                .addClass('o_tooltip_title')
                .html(title)
                .appendTo($tooltip);
            $('<div>')
                .addClass('o_tooltip_content')
                .html(value)
                .appendTo($tooltip);
            return $tooltip[0].outerHTML;
        },

        on_fold_action: function(e) {
            var $e = $(e.currentTarget),
                $action = $e.parents('.oe_board_widget:first'),
                id = parseInt($action.attr('data-id'), 10);
            $e.toggleClass('oe_minimize oe_maximize');
            $action.find('.oe_board_widget_content').toggle();
        },

        on_dashboard_action_clicked: function (ev) {
            ev.preventDefault();
            var self = this,
                $action = $(ev.currentTarget),
                action_name = $action.attr('name'),
                action_menu_id = $action.data('menu_id') || null,
                def = $.Deferred();
            if (action_menu_id) {
                new Model("ir.model.data")
                    .call("xmlid_to_res_id", [action_menu_id])
                    .then(function (data) {
                        if (data) {
                            action_menu_id = data;
                            var menu = new XopgiBoard.Menu(self);
                            menu.setElement(self.$el.parents().find('.oe_application_menu_placeholder'));
                            menu.start();
                            menu.is_bound.then(function() {
                                $.when(menu.open_menu(action_menu_id)).then(function(){
                                    def.resolve();
                                });
                            });
                        }
                    });
            }
            else {
                def.resolve();
            }
            return $.when(def)
                .then(function () {
                    if (action_name) {
                        var options = {
                            action_menu_id: action_menu_id,
                            additional_context: pyeval.eval(
                                'context', $action.data('context'), {}) || {}
                        };
                        new Model("ir.model.data")
                            .call("xmlid_to_res_id", [action_name])
                            .then(function (data) {
                                if (data) {
                                    self.do_action(data, options);
                                }
                            });
                    }
                });
        },

        on_change_input_target: function (e) {
            var self = this;
            var $input = $(e.target);
            var target_name = $input.attr('name');
            var target_value = $input.val();
            var target_mode = $input.data('mode');
            var old_value = $input.data('value');
            if (!!target_value && isNaN(target_value)) {
                this.do_warn(_t("Wrong value entered!"),
                             _t("Only Integer Value should be valid."));
            } else if (old_value == target_value){
                var target_text = target_value ?
                    self.humanFriendlyNumber(target_value) :
                    _t('Click to set');
                var $span = $('<span>' + target_text + '</span>');
                $span.attr('name', target_name);
                $span.attr('class', 'o_target_to_set');
                $span.attr('title', _t('Click to set'));
                $span.attr('value', target_value);
                $.when(self._updated).then(function () {
                    $span.replaceAll(self.$('.oe_changing[name=' + target_name + ']'));
                });
            } else {
                this._updated = new Model('xopgi.board')
                    .call('modify_target_dashboard',
                          [target_name, target_value, target_mode])
                    .then(function () {
                        self.do_reload();
                    });
            }
        },

        on_dashboard_target_clicked: function (ev) {
            if (this.show_demo) {
                // The user is not allowed to modify the targets in demo mode
                return;
            }
            var self = this;
            var $target = $(ev.currentTarget);
            var target_name = $target.attr('name');
            var target_value = $target.attr('value');
            var old_value = $target.attr('value') || '';
            var target_mode = $target.data('mode');
            var $input = $('<input/>', {type: "text"});
            $input.attr('class', 'oe_changing');
            $input.attr('name', target_name);
            $input.data('mode', target_mode);
            $input.data('value', old_value);
            if (target_value) {
                $input.attr('value', target_value);
            }
            $input.on('keyup input', function (e) {
                if (e.which === $.ui.keyCode.ENTER) {
                    self.on_change_input_target(e);
                }
            });
            $input.on('blur', function (e) {
                self.on_change_input_target(e);
            });
            $.when(this._updated).then(function () {
                $input.replaceAll(
                    self.$('.o_target_to_set[name=' + target_name + ']'))
                    .focus()
                    .select();
            });
        },

        do_reload: function () {
            this.do_action({type: 'ir.actions.client', tag: 'reload'});
        },

        humanFriendlyNumber: function(a, c){
            a = a || 0;
            if (-1000 < a && a < 1000){
                if (!!c){
                    return this.formatCurrency(a, c);
                }
                else{
                    return Math.round(a);
                }
            }
            if (!!a && a < 0) {
                return '-' + humanFriendlyNumber(a*-1, 0);
            }
            else{
                return humanFriendlyNumber(a, 0);
            }
        },

        getTooltipText: function (a, t, c) {
            a = a || 0;
            if (!!c) {
                a = this.formatCurrency(a, c);
            }
            if (!!t){
                if (-1000 < a && a < 1000) {
                    return _t(t);
                }
                else{
                    return a + ': ' + _t(t);
                }
            }
            else {
                return a;
            }
        }
    });

    core.form_tag_registry.add('xopgi_board', XopgiBoard);

    CalendarView.include({

        view_loading: function (r) {
            var context_mode = this.dataset.context['default_mode'];
            if (!!context_mode && (context_mode == 'day' ||
                                   context_mode == 'week' ||
                                   context_mode == 'month')) {
                r.arch.attrs.mode = context_mode;
            }
            return this._super(r);
        }
    });

    XopgiBoard.Menu = Menu.extend({
        destroy: function () {
            /* This is necessary to avoid main menu drop when leave a
               instanced menu from board.
            */
        }
    });
});
