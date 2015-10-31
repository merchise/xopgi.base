openerp.xopgi_sale_board = function(instance) {

var Model = instance.web.Model;
    var _t = instance.web.core._t;

instance.web.form.XopgiBoard.include({
    events: {
        'click .o_dashboard_action': 'on_dashboard_action_clicked',
        'click .o_target_to_set': 'on_dashboard_target_clicked',
    },


    on_dashboard_action_clicked: function (ev) {
        ev.preventDefault();

        var self = this;
        var $action = $(ev.currentTarget);
        var action_name = $action.attr('name');
        var action_extra = $action.data('extra');
        var additional_context = {}

        // TODO: find a better way to add defaults to search view
        if (action_name === 'calendar.action_calendar_event') {
            additional_context['search_default_mymeetings'] = 1;
        } else if (action_name === 'xopgi_sale_board.crm_lead_action_activities') {
            if (action_extra === 'today') {
                additional_context['search_default_today'] = 1;
            } else if (action_extra === 'this_week') {
                additional_context['search_default_this_week'] = 1;
            } else if (action_extra === 'overdue') {
                additional_context['search_default_overdue'] = 1;
            }
        } else if (action_name === 'crm.crm_opportunity_report_action_graph') {
            additional_context['search_default_won'] = 1;
        }

        new Model("ir.model.data")
            .call("xmlid_to_res_id", [action_name])
            .then(function (data) {
                if (data) {
                    self.do_action(data, {additional_context: additional_context});
                }
            });
    },

    on_change_input_target: function (e) {
        var self = this;
        var $input = $(e.target);
        var target_name = $input.attr('name');
        var target_value = $input.val();

        if (!!target_value && isNaN(target_value)) {
            this.do_warn(_t("Wrong value entered!"), _t("Only Integer Value should be valid."));
        } else {
            this._updated = new Model('crm.lead')
                .call('modify_target_sales_dashboard', [target_name, target_value])
                .then(function () {
                    target_value = target_value ? target_value : 'Click to set';
                    var $span = $('<span>'+ target_value + '</span>');
                    $span.attr('name', target_name);
                    $span.attr('class', 'o_target_to_set');
                    $span.attr('title', 'Click to set');
                    $span.attr('value', target_value);
                    $.when(self._updated).then(function () {
                        $span.replaceAll(self.$('.oe_changing[name=' + target_name + ']'));
                    });
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

        var $input = $('<input/>', {type: "text"});
        $input.attr('class', 'oe_changing');
        $input.attr('name', target_name);
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
            $input.replaceAll(self.$('.o_target_to_set[name=' + target_name + ']')) // the target may have changed (re-rendering)
                .focus()
                .select();
        });
    },

    render_monetary_field: function (value, currency_id) {
        var self = this;
        this.currency = false;
        this.get_currency_info(currency_id);
        if (this.currency) {
            var digits_precision = [69, this.currency.decimal_places || 2];
            value = instance.web.format_value(value || 0, {
                type: "float",
                digits: digits_precision
            });
            if (this.currency.position === "after") {
                value += this.currency.symbol;
            } else {
                value = this.currency.symbol + value;
            }
        }
        return value
    },

    get_currency_info: function (currency_id) {
        this.currency = {
            symbol: '$',
            position: 'after',
            decimal_places: 2
        };
        var self = this;
        if (currency_id){
            new Model("res.currency").query(
                ["symbol", "position", "decimal_places"])
                .filter([["id", "=", currency_id]]).first()
                .then(function (result) {
                    self.currency = result ? result : self.currency;
                });
        }
    },
});

};
