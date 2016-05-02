(function () {
    "use strict";

    var QWeb = openerp.qweb;
    var notification_bus = openerp.notification_bus = {};

    notification_bus.bus = openerp.Widget.extend({

        init: function (parent, options) {
            this._super(parent);
            this.options = _.clone(options) || {};

            // business
            var bus = this.bus = new openerp.bus.Bus();
            bus.on('notification', this, this.on_notification);
        },

        start: function () {
            this.bus.start_polling();
            return this._super.apply(this, arguments);
        },

        on_notification: function (notification) {
            var self = this;
            var channel = notification[0];
            var message = notification[1];

            if (Array.isArray(channel) && (channel[1] === 'res_user_notify' || channel[1] === 'res_user_warn')) {
                self.received_message(channel[1], message);
            }
        },

        received_message: function (channel, message) {
            var self = this,
                a,
                notif_box = $.find(".e_web_id_" + message.id);
            if (!notif_box.length) {
                console.log(message);
                var title = QWeb.render('web_notify_title', {
                    'title': message.title,
                    'id': message.id
                });
                var body = QWeb.render('web_notify_body', {
                    'message': message.body
                });
                if (channel == 'res_user_notify') {
                    a = openerp.client.do_notify(title, body, true);
                }
                else {
                    a = openerp.client.do_warn(title, body, true);
                }
                a.element.find(".link2recall")
                    .on('click',
                        function () {
                            self.get_web_notif_box(this)
                                .find('.ui-notify-close')
                                .trigger("click");
                        });
                a.element.find(".link2showed")
                    .on('click',
                        function () {
                            self.get_web_notif_box(this)
                                .find('.ui-notify-close')
                                .trigger("click");
                        });
            }
            else if (self.get_web_notif_box(notif_box).attr("style") !== "") {
                self.get_web_notif_box(notif_box).attr("style", "");
            }
        },

        get_web_notif_box: function (me) {
            return $(me).closest(".ui-notify-message-style");
        }
    });

    openerp.web.WebClient.include({
        show_application: function () {
            this._super.apply(this, arguments);
            var bus = new notification_bus.bus();
            openerp.notification_bus.single = bus;
            bus.appendTo(openerp.client.$el);
        }
    });

    return notification_bus;
})();