openerp.xopgi_sale_board = function(instance) {

var Model = instance.web.Model;
    var _t = instance.web.core._t;

instance.web.form.XopgiBoard.include({
    events: {
        'click .o_target_to_set': 'on_dashboard_target_clicked',
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
});

};
