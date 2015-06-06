{
    'name': 'Many2One Selection Widget',
    'category': 'Hidden',
    'description': """
Many2One Selection Widget.
==========================

""",
    'version': '2.0',
    'depends': ['web'],
    'data': [
        'views/web_m2o_selection.xml',
    ],
    'qweb': [
        'static/src/xml/many2one_selection.xml',
    ],
    'auto_install': True
}
