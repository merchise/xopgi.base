odoo.define('widget_m2o_default_choices.m2o_default_choices', function (require){

    var core = require('web.core');
    var data = require('web.data');
    var FieldMany2One = core.form_widget_registry.get('many2one');

    var _t = core._t;

    var FieldMany2OneDefaultChoices = FieldMany2One.extend({
        init: function (field_manager, node) {
            this._super(field_manager, node);
        },
        get_search_result: function (search_val) {
            var len = search_val.length
            if (this.node.attrs.priority_domain && len == 0) {
                return this.get_default_choices(search_val)
            }
            else {
                return this._super(search_val)
            }
        },
        get_default_choices: function (search_val) {
            var self = this;
            var dataset = new data.DataSet(this, this.field.relation, self.build_context());
            var blacklist = this.get_search_blacklist();
            return this.orderer.add(dataset.name_search(
                search_val, new data.CompoundDomain(self.build_priority_domain(), [["id", "not in", blacklist]]),
                'ilike', 160, self.build_context())).then(function (data) {
                var values = _.map(data, function (x) {
                    x[1] = x[1].split("\n")[0];
                    return {
                        label: _.str.escapeHTML(x[1]),
                        value: x[1],
                        name: x[1],
                        id: x[0]
                    };
                });

                // search more... show all possibilities
                values.push({
                    label: _t("Search More..."),
                    action: function () {
                        dataset.name_search(search_val, self.build_domain(), 'ilike', 160).done(function (data) {
                            self._search_create_popup("search", data);
                        });
                    },
                    classname: 'oe_m2o_dropdown_option'
                });

                // quick create
                var raw_result = _(data.result).map(function (x) {
                    return x[1];
                });
                if (search_val.length > 0 && !_.include(raw_result, search_val) && !(self.options && (self.options.no_create || self.options.no_quick_create))) {
                    values.push({
                        label: _.str.sprintf(_t('Create "<strong>%s</strong>"'),
                            $('<span />').text(search_val).html()),
                        action: function () {
                            self._quick_create(search_val);
                        },
                        classname: 'oe_m2o_dropdown_option'
                    });
                }
                // create...
                if (!(self.options && (self.options.no_create || self.options.no_create_edit))) {
                    values.push({
                        label: _t("Create and Edit..."),
                        action: function () {
                            self._search_create_popup("form", undefined, self._create_context(search_val));
                        },
                        classname: 'oe_m2o_dropdown_option'
                    });
                }
                else if (values.length == 0)
                    values.push({
                        label: _t("No results to show..."),
                        action: function () {
                        },
                        classname: 'oe_m2o_dropdown_option'
                    });
                return values;
            })
        },
        build_priority_domain: function () {
            var priority_domain = this.node.attrs.priority_domain || [];
            var final_domain = this.build_domain();
            final_domain.add(priority_domain);
            return final_domain;
        }
    });

    core.form_widget_registry.add('many2one_default_choices', FieldMany2OneDefaultChoices);

})

