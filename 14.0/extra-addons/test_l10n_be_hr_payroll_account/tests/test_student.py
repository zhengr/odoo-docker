# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime, date
from collections import OrderedDict

from odoo.tools.float_utils import float_compare
from odoo.tests import common, tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install', 'student')
class TestStudent(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref='l10n_be.l10nbe_chart_template'):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.company_data['company'].country_id = cls.env.ref('base.be')

        cls.new_calendar = cls.env['resource.calendar'].create({
            'name': 'O h/w calendar',
            'company_id': cls.env.company.id,
            'hours_per_day': 9,
            'full_time_required_hours': 0,
            'attendance_ids': [(5, 0, 0)],
        })

        cls.employee = cls.env['hr.employee'].create({
            'name': 'Jean-Pol Student',
            'company_id': cls.env.company.id,
            'resource_calendar_id': cls.new_calendar.id,
        })

        cls.contract = cls.env['hr.contract'].create({
            'employee_id': cls.employee.id,
            'company_id': cls.env.company.id,
            'name': 'Jean-Pol Student Contract',
            'state': 'open',
            'date_start': date(2015, 1, 1),
            'resource_calendar_id': cls.new_calendar.id,
            'structure_type_id': cls.env.ref('l10n_be_hr_payroll.structure_type_student').id,
            'wage': 0,
            'hourly_wage': 10.8714,
            'fuel_card': 0,
            'meal_voucher_amount': 7.45,
            'representation_fees': 0,
            'commission_on_target': 0,
            'ip_wage_rate': 0,
            'ip': False,
            'transport_mode_private_car': True,
            'km_home_work': 25,
            'internet': 0,
            'mobile': 0,
        })

    def test_student(self):
        # CASE: Worked 6 days
        attendance_work_entry_type = self.env.ref('hr_work_entry.work_entry_type_attendance')
        vals_list = [
            (datetime(2020, 9, 1, 9, 0), datetime(2020, 9, 1, 18, 0)),
            (datetime(2020, 9, 2, 9, 0), datetime(2020, 9, 2, 18, 0)),
            (datetime(2020, 9, 3, 9, 0), datetime(2020, 9, 3, 18, 0)),
            (datetime(2020, 9, 4, 9, 0), datetime(2020, 9, 4, 18, 0)),
            (datetime(2020, 9, 7, 9, 0), datetime(2020, 9, 7, 18, 0)),
            (datetime(2020, 9, 8, 9, 0), datetime(2020, 9, 8, 18, 0)),
        ]
        work_entries = self.env['hr.work.entry'].create([{
            'name': 'Attendance',
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'work_entry_type_id': attendance_work_entry_type.id,
            'date_start': vals[0],
            'date_stop': vals[1],
            'company_id': self.env.company.id,
            'state': 'draft',
        } for vals in vals_list])

        payslip = self.env['hr.payslip'].with_context(allowed_company_ids=self.env.company.ids).new({
            'employee_id': self.employee.id,
            'date_from': date(2020, 9, 1),
            'date_to': date(2020, 9, 30),
        })
        payslip._onchange_employee()

        self.assertEqual(len(payslip.worked_days_line_ids), 1)
        self.assertEqual(payslip.worked_days_line_ids.number_of_hours, 54)
        self.assertEqual(payslip.worked_days_line_ids.number_of_days, 6)

        payslip.compute_sheet()

        self.assertEqual(len(payslip.line_ids), 6)
        self.assertAlmostEqual(payslip._get_salary_line_total('BASIC'), 586.98, places=2)
        self.assertAlmostEqual(payslip._get_salary_line_total('ONSS'), -15.91, places=2)
        self.assertAlmostEqual(payslip._get_salary_line_total('GROSS'), 571.07, places=2)
        self.assertAlmostEqual(payslip._get_salary_line_total('CAR.PRIV'), 13.86, places=2)
        self.assertAlmostEqual(payslip._get_salary_line_total('MEAL_V_EMP'), -6.54, places=2)
        self.assertAlmostEqual(payslip._get_salary_line_total('NET'), 578.39, places=2)
