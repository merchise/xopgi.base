odoo.define('xopgi.base.WebNotification', function (require) {
    'use strict';

    var WebClient = require('web.WebClient');
    var core = require('web.core');
    var bus = require('bus.bus').bus;
    var QWeb = core.qweb;

    WebClient.include({
        start: function () {
            var self = this;
            var res = this._super.apply(this, arguments);
            bus.on('notification', this, this.on_notification);
            return res;
        },

        on_notification: function (notifications) {
            var self = this;
            _.each(notifications, function (notification) {
                var channel = notification[0][1];
                var message = notification[1];
                if(channel && channel === 'res_user_notify' || channel === 'res_user_warn')
                    self.received_message(channel, message);
            });
        },

        received_message: function (channel, message) {
            var self = this,
                notif_box = $.find(".e_web_id_" + message.id);
            if (notif_box.length) {
                var msg = self.get_web_notif_box(notif_box).remove();
            }
            var title = QWeb.render('WebNotifications.web_notify_title', {
                'title': message.title,
                'id': message.id
            });
            var body = QWeb.render('WebNotifications.web_notify_body', {
                'message': message.body,
                'actions': message.actions
            });
            if (channel == 'res_user_notify' && message.type_notify != 'alarm') {
                self.do_notify(title, body, true);
            }
            else {
                self.do_warn(title, body, true);
            }
            this.$el.find(".web_notification_action").on('click', function (ev) {
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
                $.when(def).then(function(){
                    self.action_manager.do_action(action);
                });
            });
        },

        get_web_notif_box: function (me) {
            return $(me).closest(".ui-notify-message-style");
        }

    });


});

// Local Variables:
// indent-tabs-mode: nil
// End:
