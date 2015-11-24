openerp.xopgi_board = function(instance) {
var QWeb = instance.web.qweb,
    Model = instance.web.Model;

instance.xopgi_board = instance.xopgi_board || {};

instance.web.form.XopgiBoard = instance.web.form.FormWidget.extend({
    init: function(view, node) {
        view.ViewManager.$('.oe_view_manager_buttons').hide();
        var $webclient = view.$el.parents('.oe_webclient');
        $webclient.find('.oe_leftbar').hide();
        this._super(view, node);
    },

    start: function() {
        this._super.apply(this, arguments);

        var self = this;

        this.render();
        // Events
        this.$el.delegate('.oe_board_container .oe_fold',
                          'click', this.on_fold_action);
        this.$el.delegate('.o_dashboard_action', 'click',
                          this.on_dashboard_action_clicked);
        this.$el.delegate('.o_target_to_set', 'click',
                          this.on_dashboard_target_clicked);
        // Get the function to format currencies
        new instance.web.Model("res.currency")
            .call("get_format_currencies_js_function")
            .then(function (data) {
                self.formatCurrency = new Function("amount, currency_id", data);
            });
    },

    fetch_data: function () {
        var board = new instance.web.Model('xopgi.board');
        var context = new instance.web.CompoundContext(board.context() || []);
        return board.call('get_board_widgets', [context]);
    },

    render: function () {
        var self = this;

        return this.fetch_data().then(function (result) {
            var dashboard = QWeb.render('xopgi.board', {
                widget: self,
                values: result,
            });
            $(dashboard).prependTo(self.$el);
            _.each(result, function(category){
                _.each(category, function (values) {
                    var template_name = '';
                    if (!!values.template_name) {
                        template_name = values.template_name
                    } else {
                        template_name = 'no_content'
                    }
                    if (!!values.xml_template) {
                        QWeb.add_template(values.xml_template);
                    }
                    var args = values;
                    args.widget = self;
                    var template = QWeb.render(template_name, args);
                    var selector = '.oe_' + template_name.replace('.', '_');
                    self.$el.find(selector).append(template);
                })
            });
        });
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

        var self = this;
        var $action = $(ev.currentTarget);
        var action_name = $action.attr('name');
        var options = {
            action_menu_id: $action.data('menu_id') || null,
            additional_context: instance.web.pyeval.eval(
                'context', $action.data('context'), {}) || {},
        };
        new Model("ir.model.data")
            .call("xmlid_to_res_id", [action_name])
            .then(function (data) {
                if (data) {
                    self.do_action(data, options);
                }
            });
    },

    on_change_input_target: function (e) {
        var self = this;
        var $input = $(e.target);
        var target_name = $input.attr('name');
        var target_value = $input.val();
        var target_mode = $input.data('mode');

        if (!!target_value && isNaN(target_value)) {
            this.do_warn(_t("Wrong value entered!"),
                         _t("Only Integer Value should be valid."));
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
        var target_mode = $target.data('mode');
        var $input = $('<input/>', {type: "text"});
        $input.attr('class', 'oe_changing');
        $input.attr('name', target_name);
        $input.data('mode', target_mode);
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
        var view_manager = this.view.getParent(),
            action_manager = view_manager.getParent();
        this.view.destroy();
        action_manager.do_action(view_manager.action);
    }
});

instance.web.form.tags.add('xopgi_board', 'instance.web.form.XopgiBoard');


};
