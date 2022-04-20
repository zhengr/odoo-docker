# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo.tests.common import SavepointCase, tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install', 'sample_payslip')
class TestSamplePayslip(AccountTestInvoicingCommon):

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
            'hours_per_week': 38.00000000000001,
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

        cls.leaves = cls.env['resource.calendar.leaves'].create([{
            'name': "Absence",
            'calendar_id': cls.resource_calendar.id,
            'company_id': cls.env.company.id,
            'resource_id': cls.employee.resource_id.id,
            'date_from': datetime.datetime(2020, 9, 2, 6, 0, 0),
            'date_to': datetime.datetime(2020, 9, 3, 14, 36, 0),
            'time_type': "leave",
            'work_entry_type_id': cls.env.ref('hr_work_entry_contract.work_entry_type_sick_leave').id
        }])

        cls.brand = cls.env['fleet.vehicle.model.brand'].create([{
            'name': "Test Brand"
        }])

        cls.model = cls.env['fleet.vehicle.model'].create([{
            'name': "Test Model",
            'brand_id': cls.brand.id,
        }])

        cls.car = cls.env['fleet.vehicle'].create([{
            'name': "Test Car",
            'license_plate': "TEST",
            'driver_id': cls.employee.address_home_id.id,
            'company_id': cls.env.company.id,
            'model_id': cls.model.id,
            'first_contract_date': datetime.date(2020, 10, 5),
            'co2': 88.0,
            'car_value': 38000.0,
            'fuel_type': "diesel",
            'acquisition_date': datetime.date(2020, 1, 1)
        }])

        cls.contracts = cls.env['fleet.vehicle.log.contract'].create([{
            'name': "Test Contract",
            'vehicle_id': cls.car.id,
            'company_id': cls.env.company.id,
            'start_date': datetime.date(2020, 10, 5),
            'expiration_date': datetime.date(2021, 10, 5),
            'state': "open",
            'cost_generated': 0.0,
            'cost_frequency': "monthly",
            'recurring_cost_amount_depreciated': 0.0
        }, {
            'name': "Test Contract",
            'vehicle_id': cls.car.id,
            'company_id': cls.env.company.id,
            'start_date': datetime.date(2020, 10, 5),
            'expiration_date': datetime.date(2021, 10, 5),
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
            'hourly_wage': 0.0,
            'holidays': 0.0,
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
            'ip': False,
            'ip_wage_rate': 25.0,
            'time_credit': False,
            'work_time_rate': False,
            'fiscal_voluntarism': False,
            'fiscal_voluntary_rate': 0.0
        }])

        cls.payslip = cls.env['hr.payslip'].create([{
            'name': "Test Payslip",
            'employee_id': cls.employee.id,
            'contract_id': cls.contract.id,
            'company_id': cls.env.company.id,
            'vehicle_id': cls.car.id,
            'struct_id': cls.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_employee_salary').id,
            'date_from': datetime.date(2020, 9, 1),
            'date_to': datetime.date(2020, 9, 30)
        }])

    def test_sample_payslip(self):
        work_entries = self.contract._generate_work_entries(datetime.date(2020, 9, 1), datetime.date(2020, 9, 30))
        work_entries.action_validate()
        self.payslip._onchange_employee()
        self.payslip.compute_sheet()

        self.assertEqual(len(self.payslip.worked_days_line_ids), 2)
        self.assertEqual(len(self.payslip.input_line_ids), 0)
        self.assertEqual(len(self.payslip.line_ids), 15)

        self.assertAlmostEqual(self.payslip._get_salary_line_total('BASIC'), 2650.0, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('ATN.INT'), 5.0, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('ATN.MOB'), 4.0, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('SALARY'), 2659.0, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('ONSS'), -347.53, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('GROSS'), 2452.61, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('P.P'), -542.93, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('ATN.INT.2'), -5.0, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('ATN.MOB.2'), -4.0, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('M.ONSS'), -23.66, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('MEAL_V_EMP'), -21.8, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('REP.FEES'), 150.0, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('NET'), 1864.08, places=2)


    def test_edit_payslip_lines(self):
        """
        Test the edtion of payslip lines in this sample payslip
        We want to edit the amount of the payslip line containing ATN.INT as code.
        After the edition, we recompute the following payslip lines and we check if the payslip line containing the ATN.INT.2 as code
        has been edited. It should be the opposite amount of the ATN.INT.
        We also want to edit hte amount of the payslip line containing ATN.MOB as code.
        Same process than the previous edition.
        After these both editions, we need to check if all payslip lines are correct and we have the expected total for the NET SALARY.
        """
        work_entries = self.contract._generate_work_entries(datetime.date(2020, 9, 1), datetime.date(2020, 9, 30))
        work_entries.action_validate()
        self.payslip._onchange_employee()
        self.payslip.compute_sheet()

        action = self.payslip.action_edit_payslip_lines()
        wizard = self.env[action['res_model']].browse(action['res_id'])

        # Edit the amount of the payslip line with the ATN.INT code
        atn_int_line = wizard.line_ids.filtered(lambda line: line.code == 'ATN.INT')
        atn_int_line.amount = 6.0
        wizard.recompute_following_lines(atn_int_line.id)
        self.assertEqual(atn_int_line.amount, 6.0)
        self.assertAlmostEqual(atn_int_line.total, 6.0, places=2)

        # Check if the ATN.INT.2 has also been edited
        atn_int_2_line = wizard.line_ids.filtered(lambda line: line.code == 'ATN.INT.2')
        self.assertEqual(atn_int_2_line.amount, -atn_int_line.amount)
        self.assertAlmostEqual(atn_int_2_line.total, -6.0, places=2)

        # Edit the amount of the payslip line with the ATN.MOB code
        atn_mob_line = wizard.line_ids.filtered(lambda line: line.code == 'ATN.MOB')
        atn_mob_line.amount = 5.0
        wizard.recompute_following_lines(atn_mob_line.id)
        self.assertEqual(atn_mob_line.amount, 5.0)
        self.assertAlmostEqual(atn_mob_line.total, 5.0, places=2)

        # Check if the ATN.MOB.2
        atn_mob_2_line = wizard.line_ids.filtered(lambda line: line.code == 'ATN.MOB.2')
        self.assertEqual(atn_mob_2_line.amount, -5.0)
        self.assertAlmostEqual(atn_mob_2_line.total, -5.0, places=2)

        # Check if the payslip is correctly recomputed
        wizard.action_validate_edition()
        self.assertAlmostEqual(self.payslip._get_salary_line_total('BASIC'), 2650.0, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('ATN.INT'), 6.0, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('ATN.MOB'), 5.0, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('SALARY'), 2661.0, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('ONSS'), -347.79, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('ATN.CAR'), 141.14, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('GROSS'), 2454.35, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('P.P'), -542.93, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('ATN.CAR.2'), -141.14, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('ATN.INT.2'), -6.0, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('ATN.MOB.2'), -5.0, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('M.ONSS'), -23.66, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('MEAL_V_EMP'), -21.8, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('REP.FEES'), 150.0, places=2)
        self.assertAlmostEqual(self.payslip._get_salary_line_total('NET'), 1863.82, places=2)
