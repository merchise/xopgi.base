{
    'name': 'Many2One Selection Widget',
    'category': 'Hidden',
    'version': '2.0',
    'depends': ['web'],
    'data': [
        'views/web_m2o_selection.xml',
    ],
    'qweb': [
        'static/src/xml/many2one_selection.xml',
    ],
    'auto_install': True,

    # MIGRATION POLICY: All addons are not included until someone work on them
    # and upgrade them.
    'installable': (8, 0) <= ODOO_VERSION_INFO < (9, 0),   # noqa
}
