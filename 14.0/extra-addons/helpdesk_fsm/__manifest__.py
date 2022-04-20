# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details
{
    'name': "Helpdesk FSM",
    'summary': "Allow generating fsm tasks from ticket",
    'description': """
        Convert helpdesk tickets to field service tasks.
    """,
    'category': 'Services/Helpdesk',
    'depends': ['helpdesk', 'industry_fsm'],
    'data': [
        'security/ir.model.access.csv',
        'views/helpdesk_views.xml',
        'views/project_task_views.xml',
        'wizard/create_task_views.xml',
    ],
    'demo': ['data/helpdesk_fsm_demo.xml'],
    'auto_install': True,
}