openerp.xopgi_widget_flexlist = function (instance) {
    var _t = instance.web._t;
    var forms = instance.web.form;

    var FlexDataSet = forms.Many2ManyDataSet.extend({
        reset_ids: function(ids) {
            this.set_ids(ids);
            this.to_delete = [];
            this.to_create = [];
            this.to_write = [];
            this.cache = [];
            this.delete_all = false;
            _.each(_.clone(this.running_reads), function(el) {
                el.reject();
            });
        }
    });

    forms.widgets.add(
        'many2many_flex',
        'instance.web.form.FieldOne2ManyWithAdd'
    );
    forms.FieldOne2ManyWithAdd = forms.FieldOne2Many.extend({
        init: function(field_manager, node) {
            this._super(field_manager, node);
            this.dataset = new FlexDataSet(this, this.field.relation);
            this.dataset.m2m = this;
            this.addablelist = true;
        },

        load_view: function() {
            this._super.apply(this, arguments);
            this.list_view.o2m_field = this;
        }
    });

    forms.One2ManyList.include({
        pad_table_to: function(count) {
            this._super.apply(this, arguments);
            if (this.view instanceof forms.One2ManyAddableListView) {
                // XXX: This is shamelessly stolen from
                // instance.web.form.One2ManyList in view_forms.js, but
                // changed to do_create_record()
                var self = this;
                var $newbutton = $('<a>', {href: '#'})
                    .text(_t("Add an item"))
                    .mousedown(function () {
                        // FIXME: needs to be an official API somehow
                        if (self.view.editor.is_editing()) {
                            self.view.__ignore_blur = true;
                        }
                    })
                    .click(function (e) {
                        e.preventDefault();
                        e.stopPropagation();
                        // FIXME: there should also be an API for that one
                        if (self.view.editor.form.__blur_timeout) {
                            clearTimeout(self.view.editor.form.__blur_timeout);
                            self.view.editor.form.__blur_timeout = false;
                        }
                        self.view.ensure_saved().done(function () {
                            self.view.__do_create_record();
                        });
                    });
                var $cell = this.$current.find(
                    'td.oe_form_field_one2many_list_row_add > a'
                );
                $cell.replaceWith($newbutton);
            }
        }
    });

    instance.web.views.add(
        'many2many_flex',
        'instance.web.form.One2ManyAddableListView'
    );
    forms.One2ManyAddableListView = forms.One2ManyListView.extend({
        init: function (parent, dataset, view_id, options) {
            this._super.apply(this, arguments);
            this.options.action_buttons = true;
            this.options.addable = _t('Add');
        },

        is_action_enabled: function(action) {
            return true;
        },

        __do_create_record: function() {
            // XXX: this._super is undefined here!
            forms.One2ManyListView.prototype.do_add_record.apply(
                this, arguments
            );
        },

        do_add_record: function () {
            var pop = new instance.web.form.SelectCreatePopup(this);
            pop.select_element(
                this.model,
                {
                    title: "Add: " + this.ViewManager.o2m.string,
                    no_create: this.ViewManager.o2m.options.no_create,
                },
                new instance.web.CompoundDomain(
                    this.ViewManager.o2m.build_domain(),
                    ["!", ["id", "in", _.reject(
                        this.ViewManager.o2m.dataset.ids,
                        function(i) {return i + 0 !== i}
                    )]]
                ),
                this.ViewManager.o2m.build_context()
            );
            var self = this;
            pop.on("elements_selected", self, function(element_ids) {
                var reload = false;
                _(element_ids).each(function (id) {
                    if(! _.detect(self.dataset.ids, function(x) {return x == id;})) {
                        self.dataset.set_ids(self.dataset.ids.concat([id]));
                        self.ViewManager.o2m.dataset.trigger('change');
                        reload = true;
                    }
                });
                if (reload) {
                    self.reload_content();
                }
            });
        }
    });

    forms.One2ManyViewManager.include({
        init: function(parent, dataset, views, flags) {
            this._super(parent, dataset, views, flags);
            if (parent instanceof forms.FieldOne2ManyWithAdd)
                this.registry = this.registry.extend({
                    list: 'instance.web.form.One2ManyAddableListView'
                });
        }
    });
}


// Local Variables:
// indent-tabs-mode: nil
// End:
