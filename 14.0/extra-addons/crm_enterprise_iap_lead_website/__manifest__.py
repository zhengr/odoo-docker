# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Website Visits Lead Generation Enterprise',
    'version': '1.0',
    'summary': 'Enterprise counterpart of Visits -> Leads',
    'description': 'Enterprise counterpart of Visits -> Leads',
    'category': 'Sales/CRM',
    'depends': [
        'crm_enterprise',
        'crm_iap_lead_website',
    ],
    'data': [
        'views/crm_lead_views.xml',
    ],
    'auto_install': True,
}
