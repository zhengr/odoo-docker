# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Hr Expense Extract',
    'version': '1.0',
    'category': 'Human Resources/Expenses',
    'summary': 'Extract data from expense scans to fill them automatically',
    'depends': ['hr_expense', 'iap', 'mail_enterprise', 'hr_expense_predict_product'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/expense_sample_receipt_views.xml',
        'wizard/expense_sample_register_views.xml',
        'data/config_parameter_endpoint.xml',
        'views/hr_expense_views.xml',
        'views/res_config_settings_views.xml',
        'data/update_status_cron.xml',
        'views/assets.xml',
    ],
    'auto_install': True,
    'license': 'OEEL-1',
}
