openerp.web_widget = function (instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web_widget.FieldMany2OneSelection = instance.web.form.FieldMany2One.extend({
        template: "FieldMany2OneSelection",

        init: function() {
            this._super.apply(this, arguments);
        },

        get_search_result: function(search_val) {
            var self = this;

            var dataset = new instance.web.DataSet(this, this.field.relation, self.build_context());
            var blacklist = this.get_search_blacklist();
            this.last_query = search_val;

            return this.orderer.add(dataset.name_search(
                    search_val, new instance.web.CompoundDomain(self.build_domain(), [["id", "not in", blacklist]]),
                    'ilike', this.limit + 1, self.build_context())).then(function(data) {
                    self.last_search = data;
                    // possible selections for the m2o
                    var values = _.map(data, function(x) {
                        x[1] = x[1].split("\n")[0];
                        return {
                            label: _.str.escapeHTML(x[1]),
                            value: x[1],
                            name: x[1],
                            id: x[0]
                        };
                    });

                    // search more... if more results that max
                    if (values.length > self.limit) {
                        values = values.slice(0, self.limit);
                        values.push({
                            label: _t("Search More..."),
                            action: function() {
                                dataset.name_search(search_val, self.build_domain(), 'ilike', 160).done(function(data) {
                                    self._search_create_popup("search", data);
                                });
                            },
                            classname: 'oe_m2o_dropdown_option'
                        });
                    }

                    return values;
                });
        }

    });

    instance.web.form.widgets.add('many2one_selection', 'instance.web_widget.FieldMany2OneSelection');

};

