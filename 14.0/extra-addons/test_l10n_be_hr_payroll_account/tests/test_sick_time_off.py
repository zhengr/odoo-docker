# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
import datetime
from odoo.tools.float_utils import float_compare
from odoo.tests import common, tagged
from odoo.tests.common import SavepointCase
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install', 'sick_time_off')
class TestSickTimeOff(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref='l10n_be.l10nbe_chart_template'):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.company_data['company'].country_id = cls.env.ref('base.be')

        cls.env.user.tz = 'Europe/Brussels'

        cls.address_home = cls.env['res.partner'].create([{
            'name': "Test Employee",
            'company_id': cls.env.company.id,
            'type': "private"
        }])

        cls.env.company.resource_calendar_id = cls.env['resource.calendar'].create({
            'name': 'Standard 38 hours/week',
            'company_id': cls.env.company.id,
            'hours_per_day': 7.6,
            'full_time_required_hours': 38,
            'attendance_ids': [
                (5, 0, 0),
                (0, 0, {'name': 'Monday Morning', 'dayofweek': '0', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Monday Afternoon', 'dayofweek': '0', 'hour_from': 13, 'hour_to': 16.6, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Tuesday Morning', 'dayofweek': '1', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Tuesday Afternoon', 'dayofweek': '1', 'hour_from': 13, 'hour_to': 16.6, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Wednesday Morning', 'dayofweek': '2', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Wednesday Afternoon', 'dayofweek': '2', 'hour_from': 13, 'hour_to': 16.6, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Thursday Morning', 'dayofweek': '3', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Thursday Afternoon', 'dayofweek': '3', 'hour_from': 13, 'hour_to': 16.6, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Friday Morning', 'dayofweek': '4', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Friday Afternoon', 'dayofweek': '4', 'hour_from': 13, 'hour_to': 16.6, 'day_period': 'afternoon'})
            ],
        })
        cls.resource_calendar = cls.env.company.resource_calendar_id

        cls.employee = cls.env['hr.employee'].create([{
            'name': "Test Employee",
            'address_home_id': cls.address_home.id,
            'resource_calendar_id': cls.resource_calendar.id,
            'company_id': cls.env.company.id,
            'marital': "single",
            'children': 0,
            'km_home_work': 75,
            'spouse_fiscal_status': "without_income",
            'disabled': False,
            'disabled_spouse_bool': False,
            'disabled_children_bool': False,
            'resident_bool': False,
            'disabled_children_number': 0,
            'other_dependent_people': False,
            'other_senior_dependent': 0,
            'other_disabled_senior_dependent': 0,
            'other_juniors_dependent': 0,
            'other_disabled_juniors_dependent': 0,
            'has_bicycle': False
        }])

        cls.brand = cls.env['fleet.vehicle.model.brand'].create([{
            'name': "Test Brand"
        }])

        cls.model = cls.env['fleet.vehicle.model'].create([{
            'name': "Test Model",
            'brand_id': cls.brand.id
        }])

        cls.car = cls.env['fleet.vehicle'].create([{
            'name': "Test Car",
            'license_plate': "TEST",
            'driver_id': cls.employee.address_home_id.id,
            'company_id': cls.env.company.id,
            'model_id': cls.model.id,
            'first_contract_date': datetime.date(2020, 10, 13),
            'co2': 88.0,
            'car_value': 38000.0,
            'fuel_type': "diesel",
            'acquisition_date': datetime.date(2020, 1, 1)
        }])

        cls.contracts = cls.env['fleet.vehicle.log.contract'].create([{
            'name': "Test Contract",
            'vehicle_id': cls.car.id,
            'company_id': cls.env.company.id,
            'start_date': datetime.date(2020, 10, 13),
            'expiration_date': datetime.date(2021, 10, 13),
            'state': "open",
            'cost_generated': 0.0,
            'cost_frequency': "monthly",
            'recurring_cost_amount_depreciated': 0.0
        }, {
            'name': "Test Contract",
            'vehicle_id': cls.car.id,
            'company_id': cls.env.company.id,
            'start_date': datetime.date(2020, 10, 13),
            'expiration_date': datetime.date(2021, 10, 13),
            'state': "open",
            'cost_generated': 0.0,
            'cost_frequency': "monthly",
            'recurring_cost_amount_depreciated': 450.0
        }])

        cls.contract = cls.env['hr.contract'].create([{
            'name': "Contract For Payslip Test",
            'employee_id': cls.employee.id,
            'resource_calendar_id': cls.resource_calendar.id,
            'company_id': cls.env.company.id,
            'date_generated_from': datetime.datetime(2020, 10, 1, 0, 0, 0),
            'date_generated_to': datetime.datetime(2020, 10, 1, 0, 0, 0),
            'car_id': cls.car.id,
            'structure_type_id': cls.env.ref('hr_contract.structure_type_employee_cp200').id,
            'date_start': datetime.date(2018, 12, 31),
            'date_end': False,
            'wage': 2650.0,
            'state': "open",
            'holidays': 0.0,
            'hourly_wage': 0.0,
            'transport_mode_car': True,
            'transport_mode_private_car': False,
            'transport_mode_train': False,
            'transport_mode_public': False,
            'train_transport_employee_amount': 0.0,
            'public_transport_employee_amount': 0.0,
            'others_reimbursed_amount': 0.0,
            'commission_on_target': 0.0,
            'fuel_card': 150.0,
            'internet': 38.0,
            'representation_fees': 150.0,
            'mobile': 30.0,
            'has_laptop': False,
            'meal_voucher_amount': 7.45,
            'eco_checks': 250.0,
            'ip': True,
            'ip_wage_rate': 25.0,
            'time_credit': False,
            'work_time_rate': False,
            'fiscal_voluntarism': False,
            'fiscal_voluntary_rate': 0.0
        }])

        cls.sick_time_off_type = cls.env['hr.leave.type'].create({
            'name': 'Sick Time Off',
            'allocation_type': 'no',
            'work_entry_type_id': cls.env.ref('hr_work_entry_contract.work_entry_type_sick_leave').id,
        })

    def test_relapse_without_guaranteed_salary(self):
        # Sick 1 Week (1 - 7 september)
        # Back 1 week (8 - 14 september)
        # Sick 4 weeks (15 septembeer - 13 october)
        # Part time sick from the 31 calendar day since the first sick day

        sick_leave_1 = self.env['hr.leave'].new({
            'name': 'Sick Time Off 1 Week',
            'employee_id': self.employee.id,
            'holiday_status_id': self.sick_time_off_type.id,
            'request_date_from': datetime.date(2020, 9, 1),
            'request_date_to': datetime.date(2020, 9, 7),
            'request_hour_from': '7',
            'request_hour_to': '18',
            'number_of_days': 5,
        })
        sick_leave_1._compute_date_from_to()
        sick_leave_1 = self.env['hr.leave'].create(sick_leave_1._convert_to_write(sick_leave_1._cache))

        sick_leave_2 = self.env['hr.leave'].new({
            'name': 'Sick Time Off 4 Weeks',
            'employee_id': self.employee.id,
            'holiday_status_id': self.sick_time_off_type.id,
            'request_date_from': datetime.date(2020, 9, 15),
            'request_date_to': datetime.date(2020, 10, 13),
            'request_hour_from': '7',
            'request_hour_to': '18',
            'number_of_days': 24,
        })
        sick_leave_2._compute_date_from_to()
        sick_leave_2 = self.env['hr.leave'].create(sick_leave_2._convert_to_write(sick_leave_2._cache))

        (sick_leave_1 + sick_leave_2).action_validate()

        work_entries = self.employee.contract_id._generate_work_entries(datetime.date(2020, 9, 1), datetime.date(2020, 10, 31))

        attendance = self.env.ref('hr_work_entry.work_entry_type_attendance')
        sick_work_entry_type = self.env.ref('hr_work_entry_contract.work_entry_type_sick_leave')
        partial_sick_work_entry_type = self.env.ref('l10n_be_hr_payroll.work_entry_type_part_sick')

        work_entries_expected_results = {
            (1, 9): sick_work_entry_type,
            (2, 9): sick_work_entry_type,
            (3, 9): sick_work_entry_type,
            (4, 9): sick_work_entry_type,
            (7, 9): sick_work_entry_type,
            (8, 9): attendance,
            (9, 9): attendance,
            (10, 9): attendance,
            (11, 9): attendance,
            (14, 9): attendance,
            (15, 9): sick_work_entry_type,
            (16, 9): sick_work_entry_type,
            (17, 9): sick_work_entry_type,
            (18, 9): sick_work_entry_type,
            (20, 9): sick_work_entry_type,
            (21, 9): sick_work_entry_type,
            (22, 9): sick_work_entry_type,
            (23, 9): sick_work_entry_type,
            (24, 9): sick_work_entry_type,
            (25, 9): sick_work_entry_type,
            (28, 9): sick_work_entry_type,
            (29, 9): sick_work_entry_type,
            (30, 9): sick_work_entry_type,
            (1, 10): sick_work_entry_type,
            (2, 10): sick_work_entry_type,
            (5, 10): sick_work_entry_type,
            (6, 10): sick_work_entry_type,
            (7, 10): sick_work_entry_type,
            (8, 10): partial_sick_work_entry_type,
            (9, 10): partial_sick_work_entry_type,
            (9, 10): partial_sick_work_entry_type,
            (12, 10): partial_sick_work_entry_type,
            (13, 10): partial_sick_work_entry_type,
            (14, 10): attendance,
            (15, 10): attendance,
            (16, 10): attendance,
            (19, 10): attendance,
            (20, 10): attendance,
            (21, 10): attendance,
            (22, 10): attendance,
            (23, 10): attendance,
            (26, 10): attendance,
            (27, 10): attendance,
            (28, 10): attendance,
            (29, 10): attendance,
            (30, 10): attendance,
            (31, 10): attendance,
        }

        for we in work_entries:
            self.assertEqual(we.work_entry_type_id, work_entries_expected_results.get((we.date_start.day, we.date_start.month)))

        september_payslip = self.env['hr.payslip'].create([{
            'name': "Test Payslip September",
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'company_id': self.env.company.id,
            'vehicle_id': self.car.id,
            'struct_id': self.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_employee_salary').id,
            'date_from': datetime.date(2020, 9, 1),
            'date_to': datetime.date(2020, 9, 30)
        }])
        september_payslip._onchange_employee()
        september_payslip.compute_sheet()

        self.assertEqual(len(september_payslip.worked_days_line_ids), 2)
        self.assertEqual(len(september_payslip.input_line_ids), 0)
        self.assertEqual(len(september_payslip.line_ids), 19)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_amount('WORK100'), 570.77, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_amount('LEAVE110'), 2079.23, places=2)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_days('WORK100'), 5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_days('LEAVE110'), 17.0, places=2)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_hours('WORK100'), 38.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_hours('LEAVE110'), 129.2, places=2)

        self.assertAlmostEqual(september_payslip._get_salary_line_total('BASIC'), 2650.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.INT'), 5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.MOB'), 4.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('SALARY'), 2659.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ONSS'), -347.53, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('GROSSIP'), 2452.61, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP.PART'), -662.5, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('GROSS'), 1790.11, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('P.P'), -240.26, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.INT.2'), -5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.MOB.2'), -4.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('M.ONSS'), -23.66, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('MEAL_V_EMP'), -5.45, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('REP.FEES'), 150.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP'), 662.5, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP.DED'), -43.17, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('NET'), 2139.93, places=2)

        october_payslip = self.env['hr.payslip'].create([{
            'name': "Test Payslip October",
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'company_id': self.env.company.id,
            'vehicle_id': self.car.id,
            'struct_id': self.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_employee_salary').id,
            'date_from': datetime.date(2020, 10, 1),
            'date_to': datetime.date(2020, 10, 31)
        }])
        october_payslip._onchange_employee()
        october_payslip.compute_sheet()

        self.assertEqual(len(october_payslip.worked_days_line_ids), 3)
        self.assertEqual(len(october_payslip.input_line_ids), 0)
        self.assertEqual(len(october_payslip.line_ids), 21)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('WORK100'), 1549.23, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('LEAVE110'), 611.54, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('LEAVE214'), 0.0, places=2)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('WORK100'), 13.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('LEAVE110'), 5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('LEAVE214'), 4.0, places=2)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('WORK100'), 98.8, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('LEAVE110'), 38.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('LEAVE214'), 30.4, places=2)

        self.assertAlmostEqual(october_payslip._get_salary_line_total('BASIC'), 2160.77, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.INT'), 5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.MOB'), 4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('SALARY'), 2169.77, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ONSS'), -283.59, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('EmpBonus.1'), 85.74, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('GROSSIP'), 2113.07, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP.PART'), -540.19, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('GROSS'), 1572.88, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('P.P'), -143.96, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('P.P.DED'), 28.42, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.INT.2'), -5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.MOB.2'), -4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('M.ONSS'), -16.37, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('MEAL_V_EMP'), -14.17, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('REP.FEES'), 122.31, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP'), 540.19, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP.DED'), -35.2, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('NET'), 1903.95, places=2)

    def test_relapse_with_guaranteed_salary(self):
        # Sick 1 Week (1 - 2 september)
        # Back 1 week (3 - 18 september)
        # Sick 2.5 weeks (21 septembeer - 7 october)
        # No part time sick as there is at least 15 days between the 2 sick time offs

        sick_leave_1 = self.env['hr.leave'].new({
            'name': 'Sick Time Off 2 Days',
            'employee_id': self.employee.id,
            'holiday_status_id': self.sick_time_off_type.id,
            'request_date_from': datetime.date(2020, 9, 1),
            'request_date_to': datetime.date(2020, 9, 2),
            'request_hour_from': '7',
            'request_hour_to': '18',
            'number_of_days': 2,
        })
        sick_leave_1._compute_date_from_to()
        sick_leave_1 = self.env['hr.leave'].create(sick_leave_1._convert_to_write(sick_leave_1._cache))

        sick_leave_2 = self.env['hr.leave'].new({
            'name': 'Sick Time Off 2.5 Weeks',
            'employee_id': self.employee.id,
            'holiday_status_id': self.sick_time_off_type.id,
            'request_date_from': datetime.date(2020, 9, 21),
            'request_date_to': datetime.date(2020, 10, 7),
            'request_hour_from': '7',
            'request_hour_to': '18',
            'number_of_days': 13,
        })
        sick_leave_2._compute_date_from_to()
        sick_leave_2 = self.env['hr.leave'].create(sick_leave_2._convert_to_write(sick_leave_2._cache))

        (sick_leave_1 + sick_leave_2).action_validate()

        work_entries = self.employee.contract_id._generate_work_entries(datetime.date(2020, 9, 1), datetime.date(2020, 10, 31))

        attendance = self.env.ref('hr_work_entry.work_entry_type_attendance')
        sick_work_entry_type = self.env.ref('hr_work_entry_contract.work_entry_type_sick_leave')

        work_entries_expected_results = {
            (1, 9): sick_work_entry_type,
            (2, 9): sick_work_entry_type,
            (3, 9): attendance,
            (4, 9): attendance,
            (7, 9): attendance,
            (8, 9): attendance,
            (9, 9): attendance,
            (10, 9): attendance,
            (11, 9): attendance,
            (14, 9): attendance,
            (15, 9): attendance,
            (16, 9): attendance,
            (17, 9): attendance,
            (18, 9): attendance,
            (20, 9): attendance,
            (21, 9): sick_work_entry_type,
            (22, 9): sick_work_entry_type,
            (23, 9): sick_work_entry_type,
            (24, 9): sick_work_entry_type,
            (25, 9): sick_work_entry_type,
            (28, 9): sick_work_entry_type,
            (29, 9): sick_work_entry_type,
            (30, 9): sick_work_entry_type,
            (1, 10): sick_work_entry_type,
            (2, 10): sick_work_entry_type,
            (5, 10): sick_work_entry_type,
            (6, 10): sick_work_entry_type,
            (7, 10): sick_work_entry_type,
            (8, 10): attendance,
            (9, 10): attendance,
            (9, 10): attendance,
            (12, 10): attendance,
            (13, 10): attendance,
            (14, 10): attendance,
            (15, 10): attendance,
            (16, 10): attendance,
            (19, 10): attendance,
            (20, 10): attendance,
            (21, 10): attendance,
            (22, 10): attendance,
            (23, 10): attendance,
            (26, 10): attendance,
            (27, 10): attendance,
            (28, 10): attendance,
            (29, 10): attendance,
            (30, 10): attendance,
            (31, 10): attendance,
        }

        for w in work_entries:
            self.assertEqual(w.work_entry_type_id, work_entries_expected_results.get((w.date_start.day, w.date_start.month)))

        september_payslip = self.env['hr.payslip'].create([{
            'name': "Test Payslip September",
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'company_id': self.env.company.id,
            'vehicle_id': self.car.id,
            'struct_id': self.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_employee_salary').id,
            'date_from': datetime.date(2020, 9, 1),
            'date_to': datetime.date(2020, 9, 30)
        }])
        september_payslip._onchange_employee()
        september_payslip.compute_sheet()

        self.assertEqual(len(september_payslip.worked_days_line_ids), 2)
        self.assertEqual(len(september_payslip.input_line_ids), 0)
        self.assertEqual(len(september_payslip.line_ids), 19)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_amount('LEAVE110'), 1223.08, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_amount('WORK100'), 1426.92, places=2)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_days('LEAVE110'), 10.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_days('WORK100'), 12.0, places=2)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_hours('LEAVE110'), 76.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_hours('WORK100'), 91.2, places=2)

        self.assertAlmostEqual(september_payslip._get_salary_line_total('BASIC'), 2650.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.INT'), 5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.MOB'), 4.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('SALARY'), 2659.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ONSS'), -347.53, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('GROSSIP'), 2452.61, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP.PART'), -662.5, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('GROSS'), 1790.11, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('P.P'), -240.26, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.INT.2'), -5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.MOB.2'), -4.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('M.ONSS'), -23.66, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('MEAL_V_EMP'), -13.08, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('REP.FEES'), 150.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP'), 662.5, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP.DED'), -43.17, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('NET'), 2132.3, places=2)

        october_payslip = self.env['hr.payslip'].create([{
            'name': "Test Payslip October",
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'company_id': self.env.company.id,
            'vehicle_id': self.car.id,
            'struct_id': self.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_employee_salary').id,
            'date_from': datetime.date(2020, 10, 1),
            'date_to': datetime.date(2020, 10, 31)
        }])
        october_payslip._onchange_employee()
        october_payslip.compute_sheet()

        self.assertEqual(len(october_payslip.worked_days_line_ids), 2)
        self.assertEqual(len(october_payslip.input_line_ids), 0)
        self.assertEqual(len(october_payslip.line_ids), 19)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('LEAVE110'), 611.54, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('WORK100'), 2038.46, places=2)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('LEAVE110'), 5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('WORK100'), 17.0, places=2)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('LEAVE110'), 38.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('WORK100'), 129.2, places=2)

        self.assertAlmostEqual(october_payslip._get_salary_line_total('BASIC'), 2650.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.INT'), 5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.MOB'), 4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('SALARY'), 2659.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ONSS'), -347.53, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('GROSSIP'), 2452.61, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP.PART'), -662.5, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('GROSS'), 1790.11, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('P.P'), -240.26, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.INT.2'), -5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.MOB.2'), -4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('M.ONSS'), -23.66, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('MEAL_V_EMP'), -18.53, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('REP.FEES'), 150.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP'), 662.5, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP.DED'), -43.17, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('NET'), 2126.85, places=2)

    def test_sick_more_than_30_days(self):
        # Sick 1 september - 15 october
        # Part time sick from the 31th day

        sick_leave = self.env['hr.leave'].new({
            'name': 'Sick Time Off 33 Days',
            'employee_id': self.employee.id,
            'holiday_status_id': self.sick_time_off_type.id,
            'request_date_from': datetime.date(2020, 9, 1),
            'request_date_to': datetime.date(2020, 10, 15),
            'request_hour_from': '7',
            'request_hour_to': '18',
            'number_of_days': 33,
        })
        sick_leave._compute_date_from_to()
        sick_leave = self.env['hr.leave'].create(sick_leave._convert_to_write(sick_leave._cache))
        sick_leave.action_validate()

        work_entries = self.employee.contract_id._generate_work_entries(datetime.date(2020, 9, 1), datetime.date(2020, 10, 31))

        attendance = self.env.ref('hr_work_entry.work_entry_type_attendance')
        sick_work_entry_type = self.env.ref('hr_work_entry_contract.work_entry_type_sick_leave')
        partial_sick_work_entry_type = self.env.ref('l10n_be_hr_payroll.work_entry_type_part_sick')

        work_entries_expected_results = {
            (1, 9): sick_work_entry_type,
            (2, 9): sick_work_entry_type,
            (3, 9): sick_work_entry_type,
            (4, 9): sick_work_entry_type,
            (7, 9): sick_work_entry_type,
            (8, 9): sick_work_entry_type,
            (9, 9): sick_work_entry_type,
            (10, 9): sick_work_entry_type,
            (11, 9): sick_work_entry_type,
            (14, 9): sick_work_entry_type,
            (15, 9): sick_work_entry_type,
            (16, 9): sick_work_entry_type,
            (17, 9): sick_work_entry_type,
            (18, 9): sick_work_entry_type,
            (20, 9): sick_work_entry_type,
            (21, 9): sick_work_entry_type,
            (22, 9): sick_work_entry_type,
            (23, 9): sick_work_entry_type,
            (24, 9): sick_work_entry_type,
            (25, 9): sick_work_entry_type,
            (28, 9): sick_work_entry_type,
            (29, 9): sick_work_entry_type,
            (30, 9): sick_work_entry_type,
            (1, 10): partial_sick_work_entry_type,
            (2, 10): partial_sick_work_entry_type,
            (5, 10): partial_sick_work_entry_type,
            (6, 10): partial_sick_work_entry_type,
            (7, 10): partial_sick_work_entry_type,
            (8, 10): partial_sick_work_entry_type,
            (9, 10): partial_sick_work_entry_type,
            (9, 10): partial_sick_work_entry_type,
            (12, 10): partial_sick_work_entry_type,
            (13, 10): partial_sick_work_entry_type,
            (14, 10): partial_sick_work_entry_type,
            (15, 10): partial_sick_work_entry_type,
            (16, 10): attendance,
            (19, 10): attendance,
            (20, 10): attendance,
            (21, 10): attendance,
            (22, 10): attendance,
            (23, 10): attendance,
            (26, 10): attendance,
            (27, 10): attendance,
            (28, 10): attendance,
            (29, 10): attendance,
            (30, 10): attendance,
            (31, 10): attendance,
        }

        for w in work_entries:
            self.assertEqual(w.work_entry_type_id, work_entries_expected_results.get((w.date_start.day, w.date_start.month)))

        september_payslip = self.env['hr.payslip'].create([{
            'name': "Test Payslip September",
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'company_id': self.env.company.id,
            'vehicle_id': self.car.id,
            'struct_id': self.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_employee_salary').id,
            'date_from': datetime.date(2020, 9, 1),
            'date_to': datetime.date(2020, 9, 30)
        }])
        september_payslip._onchange_employee()
        september_payslip.compute_sheet()

        self.assertEqual(len(september_payslip.worked_days_line_ids), 1)
        self.assertEqual(len(september_payslip.input_line_ids), 0)
        self.assertEqual(len(september_payslip.line_ids), 19)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_amount('LEAVE110'), 2690.77, places=2)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_days('LEAVE110'), 22.0, places=2)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_hours('LEAVE110'), 167.2, places=2)

        self.assertAlmostEqual(september_payslip._get_salary_line_total('BASIC'), 2650.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.INT'), 5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.MOB'), 4.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('SALARY'), 2659.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ONSS'), -347.53, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('GROSSIP'), 2452.61, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP.PART'), -662.5, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('GROSS'), 1790.11, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('P.P'), -240.26, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.INT.2'), -5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.MOB.2'), -4.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('M.ONSS'), -23.66, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('MEAL_V_EMP'), 0.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('REP.FEES'), 150.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP'), 662.5, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP.DED'), -43.17, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('NET'), 2145.38, places=2)

        october_payslip = self.env['hr.payslip'].create([{
            'name': "Test Payslip October",
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'company_id': self.env.company.id,
            'vehicle_id': self.car.id,
            'struct_id': self.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_employee_salary').id,
            'date_from': datetime.date(2020, 10, 1),
            'date_to': datetime.date(2020, 10, 31)
        }])
        october_payslip._onchange_employee()
        october_payslip.compute_sheet()

        self.assertEqual(len(october_payslip.worked_days_line_ids), 2)
        self.assertEqual(len(october_payslip.input_line_ids), 0)
        self.assertEqual(len(october_payslip.line_ids), 21)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('WORK100'), 1304.62, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('LEAVE214'), 0.0, places=2)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('WORK100'), 11.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('LEAVE214'), 11.0, places=2)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('WORK100'), 83.6, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('LEAVE214'), 83.6, places=2)

        self.assertAlmostEqual(october_payslip._get_salary_line_total('BASIC'), 1304.62, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.INT'), 5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.MOB'), 4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('SALARY'), 1313.62, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ONSS'), -171.69, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('EmpBonus.1'), 171.69, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('GROSSIP'), 1454.76, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP.PART'), -326.15, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('GROSS'), 1128.6, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('P.P'), -35.89, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('P.P.DED'), 35.89, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.INT.2'), -5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.MOB.2'), -4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('M.ONSS'), 0.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('MEAL_V_EMP'), -11.99, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('REP.FEES'), 73.85, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP'), 326.15, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP.DED'), -21.24, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('NET'), 1345.23, places=2)


@tagged('post_install', '-at_install', 'sick_time_off_credit_time')
class TestSickTimeOffCreditTime(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref='l10n_be.l10nbe_chart_template'):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.company_data['company'].country_id = cls.env.ref('base.be')

        cls.env.user.tz = 'Europe/Brussels'

        cls.address_home = cls.env['res.partner'].create([{
            'name': "Test Employee",
            'company_id': cls.env.company.id,
            'type': "private"
        }])

        cls.resource_calendar = cls.env['resource.calendar'].create([{
            'name': "Test Calendar",
            'company_id': cls.env.company.id,
            'attendance_ids': [(5, 0, 0)],
            'hours_per_day': 7.6,
            'tz': "Europe/Brussels",
            'two_weeks_calendar': False,
            'hours_per_week': 30.4,
            'full_time_required_hours': 38.0
        }])

        cls.global_attendances = cls.env['resource.calendar.attendance'].create([{
            'name': "Attendance",
            'calendar_id': cls.resource_calendar.id,
            'dayofweek': "0",
            'date_from': False,
            'date_to': False,
            'hour_from': 8.0,
            'hour_to': 12.0,
            'day_period': "morning",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.resource_calendar.id,
            'dayofweek': "0",
            'date_from': False,
            'date_to': False,
            'hour_from': 13.0,
            'hour_to': 16.6,
            'day_period': "afternoon",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.resource_calendar.id,
            'dayofweek': "1",
            'date_from': False,
            'date_to': False,
            'hour_from': 8.0,
            'hour_to': 12.0,
            'day_period': "morning",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.resource_calendar.id,
            'dayofweek': "1",
            'date_from': False,
            'date_to': False,
            'hour_from': 13.0,
            'hour_to': 16.6,
            'day_period': "afternoon",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.resource_calendar.id,
            'dayofweek': "3",
            'date_from': False,
            'date_to': False,
            'hour_from': 8.0,
            'hour_to': 12.0,
            'day_period': "morning",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.resource_calendar.id,
            'dayofweek': "3",
            'date_from': False,
            'date_to': False,
            'hour_from': 13.0,
            'hour_to': 16.6,
            'day_period': "afternoon",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.resource_calendar.id,
            'dayofweek': "4",
            'date_from': False,
            'date_to': False,
            'hour_from': 8.0,
            'hour_to': 12.0,
            'day_period': "morning",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.resource_calendar.id,
            'dayofweek': "4",
            'date_from': False,
            'date_to': False,
            'hour_from': 13.0,
            'hour_to': 16.6,
            'day_period': "afternoon",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }])

        cls.employee = cls.env['hr.employee'].create([{
            'name': "Test Employee",
            'address_home_id': cls.address_home.id,
            'resource_calendar_id': cls.resource_calendar.id,
            'company_id': cls.env.company.id,
            'marital': "single",
            'children': 0,
            'km_home_work': 75,
            'spouse_fiscal_status': "without_income",
            'disabled': False,
            'disabled_spouse_bool': False,
            'disabled_children_bool': False,
            'resident_bool': False,
            'disabled_children_number': 0,
            'other_dependent_people': False,
            'other_senior_dependent': 0,
            'other_disabled_senior_dependent': 0,
            'other_juniors_dependent': 0,
            'other_disabled_juniors_dependent': 0,
            'has_bicycle': False
        }])

        cls.brand = cls.env['fleet.vehicle.model.brand'].create([{
            'name': "Test Brand"
        }])

        cls.model = cls.env['fleet.vehicle.model'].create([{
            'name': "Test Model",
            'brand_id': cls.brand.id
        }])

        cls.car = cls.env['fleet.vehicle'].create([{
            'name': "Test Car",
            'license_plate': "TEST",
            'driver_id': cls.employee.address_home_id.id,
            'company_id': cls.env.company.id,
            'model_id': cls.model.id,
            'first_contract_date': datetime.date(2020, 11, 3),
            'co2': 88.0,
            'car_value': 38000.0,
            'fuel_type': "diesel",
            'acquisition_date': datetime.date(2020, 1, 1)
        }])

        cls.contracts = cls.env['fleet.vehicle.log.contract'].create([{
            'name': "Test Contract",
            'vehicle_id': cls.car.id,
            'company_id': cls.env.company.id,
            'state': "open",
            'cost_generated': 0.0,
            'recurring_cost_amount_depreciated': 0.0,
            'cost_frequency': "monthly",
            'start_date': datetime.date(2020, 11, 3),
            'expiration_date': datetime.date(2021, 11, 3)
        }, {
            'name': "Test Contract",
            'vehicle_id': cls.car.id,
            'company_id': cls.env.company.id,
            'state': "open",
            'cost_generated': 0.0,
            'recurring_cost_amount_depreciated': 450.0,
            'cost_frequency': "monthly",
            'start_date': datetime.date(2020, 11, 3),
            'expiration_date': datetime.date(2021, 11, 3)
        }])

        cls.standard_calendar = cls.env['resource.calendar'].create([{
            'name': "Test Standard Calendar",
            'company_id': cls.env.company.id,
            'attendance_ids': [(5, 0, 0)],
            'hours_per_day': 7.6,
            'tz': "Europe/Brussels",
            'two_weeks_calendar': False,
            'hours_per_week': 38.0,
            'full_time_required_hours': 38.0
        }])

        cls.standard_calendar_attendances = cls.env['resource.calendar.attendance'].create([{
            'name': "Attendance",
            'calendar_id': cls.standard_calendar.id,
            'dayofweek': "0",
            'date_from': False,
            'date_to': False,
            'hour_from': 8.0,
            'hour_to': 12.0,
            'day_period': "morning",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.standard_calendar.id,
            'dayofweek': "0",
            'date_from': False,
            'date_to': False,
            'hour_from': 13.0,
            'hour_to': 16.6,
            'day_period': "afternoon",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.standard_calendar.id,
            'dayofweek': "1",
            'date_from': False,
            'date_to': False,
            'hour_from': 8.0,
            'hour_to': 12.0,
            'day_period': "morning",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.standard_calendar.id,
            'dayofweek': "1",
            'date_from': False,
            'date_to': False,
            'hour_from': 13.0,
            'hour_to': 16.6,
            'day_period': "afternoon",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.standard_calendar.id,
            'dayofweek': "2",
            'date_from': False,
            'date_to': False,
            'hour_from': 8.0,
            'hour_to': 12.0,
            'day_period': "morning",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.standard_calendar.id,
            'dayofweek': "2",
            'date_from': False,
            'date_to': False,
            'hour_from': 13.0,
            'hour_to': 16.6,
            'day_period': "afternoon",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.standard_calendar.id,
            'dayofweek': "3",
            'date_from': False,
            'date_to': False,
            'hour_from': 8.0,
            'hour_to': 12.0,
            'day_period': "morning",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.standard_calendar.id,
            'dayofweek': "3",
            'date_from': False,
            'date_to': False,
            'hour_from': 13.0,
            'hour_to': 16.6,
            'day_period': "afternoon",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.standard_calendar.id,
            'dayofweek': "4",
            'date_from': False,
            'date_to': False,
            'hour_from': 8.0,
            'hour_to': 12.0,
            'day_period': "morning",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }, {
            'name': "Attendance",
            'calendar_id': cls.standard_calendar.id,
            'dayofweek': "4",
            'date_from': False,
            'date_to': False,
            'hour_from': 13.0,
            'hour_to': 16.6,
            'day_period': "afternoon",
            'resource_id': False,
            'week_type': False,
            'display_type': False,
            'sequence': 10,
            'work_entry_type_id': cls.env.ref('hr_work_entry.work_entry_type_attendance').id
        }])

        cls.contract = cls.env['hr.contract'].create([{
            'name': "Contract For Payslip Test",
            'employee_id': cls.employee.id,
            'resource_calendar_id': cls.resource_calendar.id,
            'company_id': cls.env.company.id,
            'date_generated_from': datetime.datetime(2020, 9, 1, 0, 0, 0),
            'date_generated_to': datetime.datetime(2020, 9, 1, 0, 0, 0),
            'car_id': cls.car.id,
            'standard_calendar_id': cls.standard_calendar.id,
            'structure_type_id': cls.env.ref('hr_contract.structure_type_employee_cp200').id,
            'date_start': datetime.date(2020, 1, 1),
            'date_end': datetime.date(2021, 9, 30),
            'wage': 2120.0,
            'state': "open",
            'holidays': 0.0,
            'hourly_wage': 0.0,
            'transport_mode_car': True,
            'transport_mode_private_car': False,
            'transport_mode_train': False,
            'transport_mode_public': False,
            'train_transport_employee_amount': 0.0,
            'public_transport_employee_amount': 0.0,
            'others_reimbursed_amount': 0.0,
            'commission_on_target': 0.0,
            'fuel_card': 150.0,
            'internet': 38.0,
            'representation_fees': 150.0,
            'mobile': 30.0,
            'has_laptop': False,
            'meal_voucher_amount': 7.45,
            'eco_checks': 250.0,
            'ip': True,
            'ip_wage_rate': 25.0,
            'time_credit': True,
            'work_time_rate': "0.8",
            'fiscal_voluntarism': False,
            'fiscal_voluntary_rate': 0.0
        }])

        cls.sick_time_off_type = cls.env['hr.leave.type'].create({
            'name': 'Sick Time Off',
            'allocation_type': 'no',
            'work_entry_type_id': cls.env.ref('hr_work_entry_contract.work_entry_type_sick_leave').id,
        })

    def test_relapse_without_guaranteed_salary_credit_time(self):
        sick_leave_1 = self.env['hr.leave'].new({
            'name': 'Sick Time Off 1 Week',
            'employee_id': self.employee.id,
            'holiday_status_id': self.sick_time_off_type.id,
            'request_date_from': datetime.date(2020, 9, 1),
            'request_date_to': datetime.date(2020, 9, 7),
            'request_hour_from': '7',
            'request_hour_to': '18',
            'number_of_days': 5,
        })
        sick_leave_1._compute_date_from_to()
        sick_leave_1 = self.env['hr.leave'].create(sick_leave_1._convert_to_write(sick_leave_1._cache))

        sick_leave_2 = self.env['hr.leave'].new({
            'name': 'Sick Time Off 4 Weeks',
            'employee_id': self.employee.id,
            'holiday_status_id': self.sick_time_off_type.id,
            'request_date_from': datetime.date(2020, 9, 15),
            'request_date_to': datetime.date(2020, 10, 13),
            'request_hour_from': '7',
            'request_hour_to': '18',
            'number_of_days': 24,
        })
        sick_leave_2._compute_date_from_to()
        sick_leave_2 = self.env['hr.leave'].create(sick_leave_2._convert_to_write(sick_leave_2._cache))

        (sick_leave_1 + sick_leave_2).action_validate()

        work_entries = self.employee.contract_id._generate_work_entries(datetime.date(2020, 9, 1), datetime.date(2020, 10, 31))

        attendance = self.env.ref('hr_work_entry.work_entry_type_attendance')
        sick_work_entry_type = self.env.ref('hr_work_entry_contract.work_entry_type_sick_leave')
        partial_sick_work_entry_type = self.env.ref('l10n_be_hr_payroll.work_entry_type_part_sick')
        credit_time_type = self.env.ref('l10n_be_hr_payroll.work_entry_type_credit_time')

        work_entries_expected_results = {
            (1, 9): sick_work_entry_type,
            (2, 9): credit_time_type,
            (3, 9): sick_work_entry_type,
            (4, 9): sick_work_entry_type,
            (7, 9): sick_work_entry_type,
            (8, 9): attendance,
            (9, 9): credit_time_type,
            (10, 9): attendance,
            (11, 9): attendance,
            (14, 9): attendance,
            (15, 9): sick_work_entry_type,
            (16, 9): credit_time_type,
            (17, 9): sick_work_entry_type,
            (18, 9): sick_work_entry_type,
            (20, 9): sick_work_entry_type,
            (21, 9): sick_work_entry_type,
            (22, 9): sick_work_entry_type,
            (23, 9): credit_time_type,
            (24, 9): sick_work_entry_type,
            (25, 9): sick_work_entry_type,
            (28, 9): sick_work_entry_type,
            (29, 9): sick_work_entry_type,
            (30, 9): credit_time_type,
            (1, 10): sick_work_entry_type,
            (2, 10): sick_work_entry_type,
            (5, 10): sick_work_entry_type,
            (6, 10): sick_work_entry_type,
            (7, 10): credit_time_type,
            (8, 10): partial_sick_work_entry_type,
            (9, 10): partial_sick_work_entry_type,
            (9, 10): partial_sick_work_entry_type,
            (12, 10): partial_sick_work_entry_type,
            (13, 10): partial_sick_work_entry_type,
            (14, 10): credit_time_type,
            (15, 10): attendance,
            (16, 10): attendance,
            (19, 10): attendance,
            (20, 10): attendance,
            (21, 10): credit_time_type,
            (22, 10): attendance,
            (23, 10): attendance,
            (26, 10): attendance,
            (27, 10): attendance,
            (28, 10): credit_time_type,
            (29, 10): attendance,
            (30, 10): attendance,
            (31, 10): attendance,
        }

        for we in work_entries:
            self.assertEqual(we.work_entry_type_id, work_entries_expected_results.get((we.date_start.day, we.date_start.month)))
        work_entries.action_validate()

        september_payslip = self.env['hr.payslip'].create([{
            'name': "Test Payslip",
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'company_id': self.env.company.id,
            'vehicle_id': self.car.id,
            'struct_id': self.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_employee_salary').id,
            'date_from': datetime.date(2020, 9, 1),
            'date_to': datetime.date(2020, 9, 30)
        }])
        september_payslip._onchange_employee()
        september_payslip.compute_sheet()

        self.assertEqual(len(september_payslip.worked_days_line_ids), 3)
        self.assertEqual(len(september_payslip.input_line_ids), 0)
        self.assertEqual(len(september_payslip.line_ids), 21)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_amount('WORK100'), 530.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_amount('LEAVE110'), 1590.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_amount('LEAVE300'), 0.0, places=2)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_days('WORK100'), 4.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_days('LEAVE110'), 13.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_days('LEAVE300'), 5.0, places=2)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_hours('WORK100'), 30.4, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_hours('LEAVE110'), 98.8, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_hours('LEAVE300'), 38.0, places=2)

        self.assertAlmostEqual(september_payslip._get_salary_line_total('BASIC'), 2120.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.INT'), 5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.MOB'), 4.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('SALARY'), 2129.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ONSS'), -278.26, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('EmpBonus.1'), 94.69, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('GROSSIP'), 2086.57, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP.PART'), -530.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('GROSS'), 1556.57, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('P.P'), -137.54, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('P.P.DED'), 31.38, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.INT.2'), -5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.MOB.2'), -4.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('M.ONSS'), -13.27, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('MEAL_V_EMP'), -4.36, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('REP.FEES'), 106.73, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP'), 530.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP.DED'), -34.53, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('NET'), 1884.84, places=2)

        october_payslip = self.env['hr.payslip'].create([{
            'name': "Test Payslip",
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'company_id': self.env.company.id,
            'vehicle_id': self.car.id,
            'struct_id': self.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_employee_salary').id,
            'date_from': datetime.date(2020, 10, 1),
            'date_to': datetime.date(2020, 10, 31)
        }])

        october_payslip._onchange_employee()
        october_payslip.compute_sheet()

        self.assertEqual(len(october_payslip.worked_days_line_ids), 4)
        self.assertEqual(len(october_payslip.input_line_ids), 0)
        self.assertEqual(len(october_payslip.line_ids), 21)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('LEAVE300'), 0.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('LEAVE110'), 489.23, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('LEAVE214'), 0.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('WORK100'), 1141.54, places=2)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('LEAVE300'), 4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('LEAVE110'), 4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('LEAVE214'), 4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('WORK100'), 10.0, places=2)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('LEAVE300'), 30.4, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('LEAVE110'), 30.4, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('LEAVE214'), 30.4, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('WORK100'), 76.0, places=2)

        self.assertAlmostEqual(october_payslip._get_salary_line_total('BASIC'), 1630.77, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.INT'), 5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.MOB'), 4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('SALARY'), 1639.77, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ONSS'), -214.32, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('EmpBonus.1'), 201.62, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('GROSSIP'), 1768.21, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP.PART'), -407.69, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('GROSS'), 1360.52, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('P.P'), -78.02, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('P.P.DED'), 66.82, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.INT.2'), -5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.MOB.2'), -4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('M.ONSS'), 0.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('MEAL_V_EMP'), -10.9, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('REP.FEES'), 80.77, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP'), 407.69, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP.DED'), -26.56, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('NET'), 1650.18, places=2)

    def test_relapse_with_guaranteed_salary_credit_time(self):
        # Sick 2 days (1 - 2 september)
        # Back 1 week (3 - 18 september)
        # Sick 2.5 weeks (21 septembeer - 7 october)
        # No part time sick as there is at least 15 days between the 2 sick time offs
        sick_leave_1 = self.env['hr.leave'].new({
            'name': 'Sick Time Off 2 Days',
            'employee_id': self.employee.id,
            'holiday_status_id': self.sick_time_off_type.id,
            'request_date_from': datetime.date(2020, 9, 1),
            'request_date_to': datetime.date(2020, 9, 2),
            'request_hour_from': '7',
            'request_hour_to': '18',
            'number_of_days': 2,
        })
        sick_leave_1._compute_date_from_to()
        sick_leave_1 = self.env['hr.leave'].create(sick_leave_1._convert_to_write(sick_leave_1._cache))

        sick_leave_2 = self.env['hr.leave'].new({
            'name': 'Sick Time Off 2.5 Weeks',
            'employee_id': self.employee.id,
            'holiday_status_id': self.sick_time_off_type.id,
            'request_date_from': datetime.date(2020, 9, 21),
            'request_date_to': datetime.date(2020, 10, 7),
            'request_hour_from': '7',
            'request_hour_to': '18',
            'number_of_days': 13,
        })
        sick_leave_2._compute_date_from_to()
        sick_leave_2 = self.env['hr.leave'].create(sick_leave_2._convert_to_write(sick_leave_2._cache))

        (sick_leave_1 + sick_leave_2).action_validate()

        work_entries = self.employee.contract_id._generate_work_entries(datetime.date(2020, 9, 1), datetime.date(2020, 10, 31))

        attendance = self.env.ref('hr_work_entry.work_entry_type_attendance')
        sick_work_entry_type = self.env.ref('hr_work_entry_contract.work_entry_type_sick_leave')
        credit_time_type = self.env.ref('l10n_be_hr_payroll.work_entry_type_credit_time')

        work_entries_expected_results = {
            (1, 9): sick_work_entry_type,
            (2, 9): credit_time_type,
            (3, 9): attendance,
            (4, 9): attendance,
            (7, 9): attendance,
            (8, 9): attendance,
            (9, 9): credit_time_type,
            (10, 9): attendance,
            (11, 9): attendance,
            (14, 9): attendance,
            (15, 9): attendance,
            (16, 9): credit_time_type,
            (17, 9): attendance,
            (18, 9): attendance,
            (20, 9): attendance,
            (21, 9): sick_work_entry_type,
            (22, 9): sick_work_entry_type,
            (23, 9): credit_time_type,
            (24, 9): sick_work_entry_type,
            (25, 9): sick_work_entry_type,
            (28, 9): sick_work_entry_type,
            (29, 9): sick_work_entry_type,
            (30, 9): credit_time_type,
            (1, 10): sick_work_entry_type,
            (2, 10): sick_work_entry_type,
            (5, 10): sick_work_entry_type,
            (6, 10): sick_work_entry_type,
            (7, 10): credit_time_type,
            (8, 10): attendance,
            (9, 10): attendance,
            (9, 10): attendance,
            (12, 10): attendance,
            (13, 10): attendance,
            (14, 10): credit_time_type,
            (15, 10): attendance,
            (16, 10): attendance,
            (19, 10): attendance,
            (20, 10): attendance,
            (21, 10): credit_time_type,
            (22, 10): attendance,
            (23, 10): attendance,
            (26, 10): attendance,
            (27, 10): attendance,
            (28, 10): credit_time_type,
            (29, 10): attendance,
            (30, 10): attendance,
            (31, 10): attendance,
        }

        for w in work_entries:
            self.assertEqual(w.work_entry_type_id, work_entries_expected_results.get((w.date_start.day, w.date_start.month)))
        work_entries.action_validate()

        september_payslip = self.env['hr.payslip'].create([{
            'name': "Test Payslip",
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'company_id': self.env.company.id,
            'vehicle_id': self.car.id,
            'struct_id': self.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_employee_salary').id,
            'date_from': datetime.date(2020, 9, 1),
            'date_to': datetime.date(2020, 9, 30)
        }])

        september_payslip._onchange_employee()
        september_payslip.compute_sheet()

        self.assertEqual(len(september_payslip.worked_days_line_ids), 3)
        self.assertEqual(len(september_payslip.input_line_ids), 0)
        self.assertEqual(len(september_payslip.line_ids), 21)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_amount('LEAVE300'), 0.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_amount('WORK100'), 1263.85, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_amount('LEAVE110'), 856.15, places=2)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_days('LEAVE300'), 5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_days('WORK100'), 10.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_days('LEAVE110'), 7.0, places=2)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_hours('LEAVE300'), 38.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_hours('WORK100'), 76.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_hours('LEAVE110'), 53.2, places=2)

        self.assertAlmostEqual(september_payslip._get_salary_line_total('BASIC'), 2120.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.INT'), 5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.MOB'), 4.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('SALARY'), 2129.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ONSS'), -278.26, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('EmpBonus.1'), 94.69, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('GROSSIP'), 2086.57, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP.PART'), -530.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('GROSS'), 1556.57, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('P.P'), -137.54, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('P.P.DED'), 31.38, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.INT.2'), -5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.MOB.2'), -4.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('M.ONSS'), -13.27, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('MEAL_V_EMP'), -10.9, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('REP.FEES'), 106.73, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP'), 530.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP.DED'), -34.53, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('NET'), 1878.3, places=2)

        october_payslip = self.env['hr.payslip'].create([{
            'name': "Test Payslip",
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'company_id': self.env.company.id,
            'vehicle_id': self.car.id,
            'struct_id': self.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_employee_salary').id,
            'date_from': datetime.date(2020, 10, 1),
            'date_to': datetime.date(2020, 10, 31)
        }])
        october_payslip._onchange_employee()
        october_payslip.compute_sheet()

        self.assertEqual(len(october_payslip.worked_days_line_ids), 3)
        self.assertEqual(len(october_payslip.input_line_ids), 0)
        self.assertEqual(len(october_payslip.line_ids), 21)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('LEAVE300'), 0.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('LEAVE110'), 489.23, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('WORK100'), 1630.77, places=2)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('LEAVE300'), 4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('LEAVE110'), 4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('WORK100'), 14.0, places=2)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('LEAVE300'), 30.4, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('LEAVE110'), 30.4, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('WORK100'), 106.4, places=2)

        self.assertAlmostEqual(october_payslip._get_salary_line_total('BASIC'), 2120.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.INT'), 5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.MOB'), 4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('SALARY'), 2129.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ONSS'), -278.26, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('EmpBonus.1'), 94.69, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('GROSSIP'), 2086.57, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP.PART'), -530.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('GROSS'), 1556.57, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('P.P'), -137.54, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('P.P.DED'), 31.38, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.INT.2'), -5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.MOB.2'), -4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('M.ONSS'), -13.27, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('MEAL_V_EMP'), -15.26, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('REP.FEES'), 115.38, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP'), 530.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP.DED'), -34.53, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('NET'), 1882.59, places=2)

    def test_sick_more_than_30_days_credit_time(self):
        # Sick 1 september - 15 october
        # Part time sick from the 31th day

        sick_leave = self.env['hr.leave'].new({
            'name': 'Sick Time Off 33 Days',
            'employee_id': self.employee.id,
            'holiday_status_id': self.sick_time_off_type.id,
            'request_date_from': datetime.date(2020, 9, 1),
            'request_date_to': datetime.date(2020, 10, 15),
            'request_hour_from': '7',
            'request_hour_to': '18',
            'number_of_days': 33,
        })
        sick_leave._compute_date_from_to()
        sick_leave = self.env['hr.leave'].create(sick_leave._convert_to_write(sick_leave._cache))
        sick_leave.action_validate()

        work_entries = self.employee.contract_id._generate_work_entries(datetime.date(2020, 9, 1), datetime.date(2020, 10, 31))

        attendance = self.env.ref('hr_work_entry.work_entry_type_attendance')
        sick_work_entry_type = self.env.ref('hr_work_entry_contract.work_entry_type_sick_leave')
        partial_sick_work_entry_type = self.env.ref('l10n_be_hr_payroll.work_entry_type_part_sick')
        credit_time_type = self.env.ref('l10n_be_hr_payroll.work_entry_type_credit_time')

        work_entries_expected_results = {
            (1, 9): sick_work_entry_type,
            (2, 9): credit_time_type,
            (3, 9): sick_work_entry_type,
            (4, 9): sick_work_entry_type,
            (7, 9): sick_work_entry_type,
            (8, 9): sick_work_entry_type,
            (9, 9): credit_time_type,
            (10, 9): sick_work_entry_type,
            (11, 9): sick_work_entry_type,
            (14, 9): sick_work_entry_type,
            (15, 9): sick_work_entry_type,
            (16, 9): credit_time_type,
            (17, 9): sick_work_entry_type,
            (18, 9): sick_work_entry_type,
            (20, 9): sick_work_entry_type,
            (21, 9): sick_work_entry_type,
            (22, 9): sick_work_entry_type,
            (23, 9): credit_time_type,
            (24, 9): sick_work_entry_type,
            (25, 9): sick_work_entry_type,
            (28, 9): sick_work_entry_type,
            (29, 9): sick_work_entry_type,
            (30, 9): credit_time_type,
            (1, 10): partial_sick_work_entry_type,
            (2, 10): partial_sick_work_entry_type,
            (5, 10): partial_sick_work_entry_type,
            (6, 10): partial_sick_work_entry_type,
            (7, 10): credit_time_type,
            (8, 10): partial_sick_work_entry_type,
            (9, 10): partial_sick_work_entry_type,
            (9, 10): partial_sick_work_entry_type,
            (12, 10): partial_sick_work_entry_type,
            (13, 10): partial_sick_work_entry_type,
            (14, 10): credit_time_type,
            (15, 10): partial_sick_work_entry_type,
            (16, 10): attendance,
            (19, 10): attendance,
            (20, 10): attendance,
            (21, 10): credit_time_type,
            (22, 10): attendance,
            (23, 10): attendance,
            (26, 10): attendance,
            (27, 10): attendance,
            (28, 10): credit_time_type,
            (29, 10): attendance,
            (30, 10): attendance,
            (31, 10): attendance,
        }

        for we in work_entries:
            self.assertEqual(we.work_entry_type_id, work_entries_expected_results.get((we.date_start.day, we.date_start.month)))

        september_payslip = self.env['hr.payslip'].create([{
            'name': "Test Payslip September",
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'company_id': self.env.company.id,
            'vehicle_id': self.car.id,
            'struct_id': self.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_employee_salary').id,
            'date_from': datetime.date(2020, 9, 1),
            'date_to': datetime.date(2020, 9, 30)
        }])
        september_payslip._onchange_employee()
        september_payslip.compute_sheet()

        self.assertEqual(len(september_payslip.worked_days_line_ids), 2)
        self.assertEqual(len(september_payslip.input_line_ids), 0)
        self.assertEqual(len(september_payslip.line_ids), 21)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_amount('LEAVE300'), 0.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_amount('LEAVE110'), 2079.23, places=2)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_days('LEAVE300'), 5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_days('LEAVE110'), 17.0, places=2)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_hours('LEAVE300'), 38.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_hours('LEAVE110'), 129.2, places=2)

        self.assertAlmostEqual(september_payslip._get_salary_line_total('BASIC'), 2120.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.INT'), 5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.MOB'), 4.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('SALARY'), 2129.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ONSS'), -278.26, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('EmpBonus.1'), 94.69, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('GROSSIP'), 2086.57, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP.PART'), -530.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('GROSS'), 1556.57, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('P.P'), -137.54, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('P.P.DED'), 31.38, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.INT.2'), -5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.MOB.2'), -4.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('M.ONSS'), -13.27, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('MEAL_V_EMP'), 0.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('REP.FEES'), 106.73, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP'), 530.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP.DED'), -34.53, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('NET'), 1889.2, places=2)

        october_payslip = self.env['hr.payslip'].create([{
            'name': "Test Payslip October",
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'company_id': self.env.company.id,
            'vehicle_id': self.car.id,
            'struct_id': self.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_employee_salary').id,
            'date_from': datetime.date(2020, 10, 1),
            'date_to': datetime.date(2020, 10, 31)
        }])
        october_payslip._onchange_employee()
        october_payslip.compute_sheet()

        self.assertEqual(len(october_payslip.worked_days_line_ids), 3)
        self.assertEqual(len(october_payslip.input_line_ids), 0)
        self.assertEqual(len(october_payslip.line_ids), 21)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('LEAVE300'), 0.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('LEAVE214'), 0.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('WORK100'), 1019.23, places=2)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('LEAVE300'), 4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('LEAVE214'), 9.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('WORK100'), 9.0, places=2)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('LEAVE300'), 30.4, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('LEAVE214'), 68.4, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('WORK100'), 68.4, places=2)

        self.assertAlmostEqual(october_payslip._get_salary_line_total('BASIC'), 1019.23, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.INT'), 5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.MOB'), 4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('SALARY'), 1028.23, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ONSS'), -134.39, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('EmpBonus.1'), 134.39, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('GROSSIP'), 1169.37, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP.PART'), -254.81, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('GROSS'), 914.57, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('P.P'), 0.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('P.P.DED'), 0.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.INT.2'), -5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.MOB.2'), -4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('M.ONSS'), 0.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('MEAL_V_EMP'), -9.81, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('REP.FEES'), 37.5, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP'), 254.81, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP.DED'), -16.59, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('NET'), 1030.33, places=2)
