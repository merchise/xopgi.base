openerp.xopgi_cdr_notification = function (instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    var FIVE_MINUTES = 5 * 60 * 1000;  // In ms for setTimeout.

    instance.web.WebClient = instance.web.WebClient.extend({
        get_cdr_notif_box: function (me) {
            return $(me).closest(".ui-notify-message-style");
        },

        get_cdr_notif: function () {
            var self = this;
            this.rpc("/xopgi_cdr_notification/notify")
                .done(
                    function (result) {
                        _.each(result, function (res) {
                            if (!($.find(".e_cdr_id_" + res.handler_id)).length) {
                                res.title = QWeb.render('cdr_notify_title', {
                                    'title': res.title,
                                    'priority': res.priority,
                                    'label': res.label,
                                    'id': res.handler_id
                                });
                                res.message = QWeb.render('cdr_notify_body', {
                                    'message': res.message
                                });
                                a = self.do_notify(res.title, res.message, true);
                                a.element.find(".link2recall")
                                    .on('click',
                                        function () {
                                            self.get_xopgi_cdr_notif_box(this)
                                                .find('.ui-notify-close')
                                                .trigger("click");
                                        });
                                a.element.find(".link2showed")
                                    .on('click',
                                        function () {
                                    self.get_xopgi_cdr_notif_box(this)
                                        .find('.ui-notify-close')
                                        .trigger("click");
                                });
                            }
                            else if (self.get_cdr_notif_box($.find(".e_cdr_id_" + res.handler_id)).attr("style") !== "") {
                                self.get_cdr_notif_box($.find(".e_cdr_id_" + res.handler_id)).attr("style", "");
                            }
                        });
                    }
                )
                .fail(function (err, ev) {
                    if (err.code === -32098) {
                        // Prevent the CrashManager to display an error
                        // in case of an xhr error not due to a server error
                        ev.preventDefault();
                    }
                });
        },

        check_cdr_notifications: function () {
            var self = this;
            self.get_cdr_notif();
            self.interval_cdr_notif = setInterval(function () {
                self.get_cdr_notif();
            }, FIVE_MINUTES);
        },

        //Override the show_application of addons/web/static/src/js/chrome.js
        show_application: function () {
            this._super();
            this.check_cdr_notifications();
        },

        //Override addons/web/static/src/js/chrome.js
        on_logout: function () {
            this._super();
            clearInterval(self.interval_cdr_notif);
        },
    });

};