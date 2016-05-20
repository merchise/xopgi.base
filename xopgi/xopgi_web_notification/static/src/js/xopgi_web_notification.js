openerp.xopgi_web_notification = function (instance) {

    var QWeb = openerp.qweb;

    instance.web.WebClient = instance.web.WebClient.extend({

        init: function (parent, options) {
            this._super(parent);
            this.options = _.clone(options) || {};

            var bus = this.notification_bus = openerp.bus.bus;
            bus.on('notification', this, this.on_notification);
        },

        on_notification: function (notifications) {
            var self = this;
            _.each(notifications, function (notification) {
                var channel = notification[0];
                var message = notification[1];

                if (Array.isArray(channel) && (channel[1] === 'res_user_notify' || channel[1] === 'res_user_warn')) {
                    self.received_message(channel[1], message);
                }
            });
        },

        received_message: function (channel, message) {
            var self = this,
                a,
                notif_box = $.find(".e_web_id_" + message.id);
            if (notif_box.length) {
                self.get_web_notif_box(notif_box).remove();
            }
            var title = QWeb.render('web_notify_title', {
                'title': message.title,
                'id': message.id
            });
            var body = QWeb.render('web_notify_body', {
                'message': message.body,
                'actions': message.actions
            });
            if (channel == 'res_user_notify') {
                a = openerp.client.do_notify(title, body, true);
            }
            else {
                a = openerp.client.do_warn(title, body, true);
            }
            a.element.find(".web_notification_action").on('click', function (ev) {
                var $target = $(ev.currentTarget),
                    action = JSON.parse($target.attr('action') || {}),
                    def = $.Deferred();
                self.get_web_notif_box(this)
                    .find('.ui-notify-close')
                    .trigger("click");
                if (action.action_id) {
                    // Do this instead call do_action directly to allow extend
                    // original action with custom values.
                    self.rpc("/web/action/load", {
                        action_id: action.action_id
                    }).then(function (data) {
                        action = _.extend(data, action);
                        def.resolve();
                    });
                }
                else
                    def.resolve();
                $.when(def)
                    .then(function () {
                        self.action_manager.do_action(action);
                    });
            });
        },

        get_web_notif_box: function (me) {
            return $(me).closest(".ui-notify-message-style");
        }
    });
};