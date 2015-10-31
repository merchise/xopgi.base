openerp.xopgi_board = function(instance) {
var QWeb = instance.web.qweb;

instance.xopgi_board = instance.xopgi_board || {};

instance.web.form.XopgiBoard = instance.web.form.FormWidget.extend({
    init: function(view, node) {
        view.ViewManager.$('.oe_view_manager_buttons').hide();
        this._super(view, node);
    },

    start: function() {
        this._super.apply(this, arguments);

        this.render();
        // Events
        this.$el.delegate('.oe_board_container .oe_fold',
                          'click', this.on_fold_action);
    },

    fetch_data: function () {
        var board = new instance.web.Model('xopgi.board');
        var context = new instance.web.CompoundContext(board.context() || []);
        return board.call('get_data', [context]);
    },

    render: function () {
        var self = this;

        return this.fetch_data().then(function (result) {
            var dashboard = QWeb.render('xopgi.board', {
                widget: self,
                values: result,
            });
            $(dashboard).prependTo(self.$el);
            _.each(result, function(values){
                var template_name = '';
                if (!!values.template) {
                    template_name = values.template
                }else{
                    template_name = 'no_content'
                }
                var args = values;
                args.widget = self;
                var template = QWeb.render(template_name, args);
                var selector = '.oe_' + template_name.replace('.', '_');
                self.$el.find(selector).append(template);
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
});

instance.web.form.tags.add('xopgi_board', 'instance.web.form.XopgiBoard');


};
