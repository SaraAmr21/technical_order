{
    'name': 'task 4',
    'version': '1.0.0',
    'category': '',
    'summary': 'Manage technical orders and order lines',
    'description': """This module helps manage technical orders and their associated order lines.""",
    'depends': ['base', 'mail', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/technical_order_view.xml',
        'data/ir_sequence_data.xml',
        'wizard/rejection_reason.xml',
        'reports/report_action.xml',
        'reports/report_template.xml',
        'views/tech_offer_view.xml',
        'data/email_template.xml',

    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
