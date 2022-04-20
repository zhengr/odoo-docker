# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests.common import tagged


@tagged('post_install', '-at_install', 'maternity_time_off')
class TestMaternityTimeOff(AccountTestInvoicingCommon):

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
            'hours_per_week': 38.0,
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
            'calendar_id': cls.resource_calendar.id,
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

        cls.public_time_off = cls.env['resource.calendar.leaves'].create([{
            'name': "Absence",
            'calendar_id': cls.resource_calendar.id,
            'company_id': cls.env.company.id,
            'date_from': datetime.datetime(2020, 10, 6, 5, 0, 0),
            'date_to': datetime.datetime(2020, 10, 6, 16, 0, 0),
            'resource_id': False,
            'time_type': "leave",
            'work_entry_type_id': cls.env.ref('l10n_be_hr_payroll.work_entry_type_bank_holiday').id
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
            'first_contract_date': datetime.date(2020, 11, 16),
            'co2': 88.0,
            'car_value': 38000.0,
            'fuel_type': "diesel",
            'acquisition_date': datetime.date(2020, 1, 1)
        }])

        cls.contracts = cls.env['fleet.vehicle.log.contract'].create([{
            'name': "Test Contract",
            'vehicle_id': cls.car.id,
            'company_id': cls.env.company.id,
            'start_date': datetime.date(2020, 11, 16),
            'expiration_date': datetime.date(2021, 11, 16),
            'state': "open",
            'cost_generated': 0.0,
            'cost_frequency': "monthly",
            'recurring_cost_amount_depreciated': 0.0
        }, {
            'name': "Test Contract",
            'vehicle_id': cls.car.id,
            'company_id': cls.env.company.id,
            'start_date': datetime.date(2020, 11, 16),
            'expiration_date': datetime.date(2021, 11, 16),
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
            'date_generated_from': datetime.datetime(2020, 9, 1, 0, 0, 0),
            'date_generated_to': datetime.datetime(2020, 9, 1, 0, 0, 0),
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

    def test_maternity_time_off(self):
        maternity_time_off = self.env['hr.leave'].new({
            'name': 'Maternity Time Off : 15 weeks',
            'employee_id': self.employee.id,
            'holiday_status_id': self.env.ref('l10n_be_hr_payroll.holiday_type_maternity').id,
            'request_date_from': datetime.date(2020, 9, 10),
            'request_date_to': datetime.date(2020, 12, 24),
            'request_hour_from': '7',
            'request_hour_to': '18',
            'number_of_days': 76,
        })
        maternity_time_off._compute_date_from_to()
        maternity_time_off = self.env['hr.leave'].create(maternity_time_off._convert_to_write(maternity_time_off._cache))

        work_entries = self.contract._generate_work_entries(datetime.date(2020, 9, 1), datetime.date(2020, 11, 30))
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

        self.assertEqual(len(september_payslip.worked_days_line_ids), 2)
        self.assertEqual(len(september_payslip.input_line_ids), 0)
        self.assertEqual(len(september_payslip.line_ids), 21)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_amount('WORK100'), 815.38, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_amount('LEAVE210'), 0.0, places=2)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_days('WORK100'), 7.0, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_days('LEAVE210'), 15.0, places=2)

        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_hours('WORK100'), 53.2, places=2)
        self.assertAlmostEqual(september_payslip._get_worked_days_line_number_of_hours('LEAVE210'), 114.0, places=2)

        self.assertAlmostEqual(september_payslip._get_salary_line_total('BASIC'), 815.38, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.INT'), 5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.MOB'), 4.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('SALARY'), 824.38, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ONSS'), -107.75, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('EmpBonus.1'), 107.75, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('GROSSIP'), 965.53, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP.PART'), -203.85, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('GROSS'), 761.68, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('P.P'), 0.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('P.P.DED'), 0.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.INT.2'), -5.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('ATN.MOB.2'), -4.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('M.ONSS'), 0.0, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('MEAL_V_EMP'), -7.63, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('REP.FEES'), 46.15, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP'), 203.85, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('IP.DED'), -13.27, places=2)
        self.assertAlmostEqual(september_payslip._get_salary_line_total('NET'), 840.64, places=2)

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

        self.assertEqual(len(october_payslip.worked_days_line_ids), 2)
        self.assertEqual(len(october_payslip.input_line_ids), 0)
        self.assertEqual(len(october_payslip.line_ids), 21)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('LEAVE500'), 122.31, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_amount('LEAVE210'), 0.0, places=2)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('LEAVE500'), 1.0, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_days('LEAVE210'), 21.0, places=2)

        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('LEAVE500'), 7.6, places=2)
        self.assertAlmostEqual(october_payslip._get_worked_days_line_number_of_hours('LEAVE210'), 159.6, places=2)

        self.assertAlmostEqual(october_payslip._get_salary_line_total('BASIC'), 122.31, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.INT'), 5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.MOB'), 4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('SALARY'), 131.31, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ONSS'), -17.16, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('EmpBonus.1'), 17.16, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('GROSSIP'), 272.45, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP.PART'), -30.58, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('GROSS'), 241.87, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('P.P'), 0.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('P.P.DED'), 0.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.INT.2'), -5.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('ATN.MOB.2'), -4.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('M.ONSS'), 0.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('MEAL_V_EMP'), 0.0, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('REP.FEES'), 4.62, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP'), 30.58, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('IP.DED'), -1.97, places=2)
        self.assertAlmostEqual(october_payslip._get_salary_line_total('NET'), 124.95, places=2)

        november_payslip = self.env['hr.payslip'].create([{
            'name': "Test Payslip",
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'company_id': self.env.company.id,
            'vehicle_id': self.car.id,
            'struct_id': self.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_employee_salary').id,
            'date_from': datetime.date(2020, 11, 1),
            'date_to': datetime.date(2020, 11, 30)
        }])

        november_payslip._onchange_employee()
        november_payslip.compute_sheet()

        self.assertEqual(len(november_payslip.worked_days_line_ids), 1)
        self.assertEqual(len(november_payslip.input_line_ids), 0)
        self.assertEqual(len(november_payslip.line_ids), 20)

        self.assertAlmostEqual(november_payslip._get_worked_days_line_amount('LEAVE210'), 0.0, places=2)

        self.assertAlmostEqual(november_payslip._get_worked_days_line_number_of_days('LEAVE210'), 21.0, places=2)

        self.assertAlmostEqual(november_payslip._get_worked_days_line_number_of_hours('LEAVE210'), 159.6, places=2)

        self.assertAlmostEqual(november_payslip._get_salary_line_total('BASIC'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('ATN.INT'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('ATN.MOB'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('SALARY'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('ONSS'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('EmpBonus.1'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('ATN.CAR'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('GROSSIP'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('IP.PART'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('GROSS'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('P.P'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('ATN.CAR.2'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('ATN.INT.2'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('ATN.MOB.2'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('M.ONSS'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('MEAL_V_EMP'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('REP.FEES'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('IP'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('IP.DED'), 0.0, places=2)
        self.assertAlmostEqual(november_payslip._get_salary_line_total('NET'), 0.0, places=2)
