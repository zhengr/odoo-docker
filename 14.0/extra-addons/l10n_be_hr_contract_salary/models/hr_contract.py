# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ast

from odoo import fields, models

EMPLOYER_ONSS = 0.2714

class HrContract(models.Model):
    _inherit = 'hr.contract'

    double_holiday_wage = fields.Monetary(compute='_compute_double_holiday_wage')
    id_card = fields.Binary(related='employee_id.id_card', groups="hr_contract.group_hr_contract_manager")
    driving_license = fields.Binary(related='employee_id.driving_license', groups="hr_contract.group_hr_contract_manager")
    mobile_invoice = fields.Binary(related='employee_id.mobile_invoice', groups="hr_contract.group_hr_contract_manager")
    sim_card = fields.Binary(related='employee_id.sim_card', groups="hr_contract.group_hr_contract_manager")
    internet_invoice = fields.Binary(related="employee_id.internet_invoice", groups="hr_contract.group_hr_contract_manager")
    double_holiday_wage = fields.Monetary(compute='_compute_double_holiday_wage')

    def _get_contract_wage_field(self):
        self.ensure_one()
        if self.structure_type_id.country_id.code == "BE":
            return 'wage_with_holidays'
        return super()._get_contract_wage_field()

    def _get_salary_costs_factor(self):
        res = super()._get_salary_costs_factor()
        if self.structure_type_id == self.env.ref('hr_contract.structure_type_employee_cp200'):
            return 13.92 + 13.0 * EMPLOYER_ONSS
        return res

    def _compute_double_holiday_wage(self):
        for contract in self:
            contract.double_holiday_wage = contract.wage_with_holidays * 0.92

    def _get_redundant_salary_data(self):
        res = super()._get_redundant_salary_data()
        cars = self.mapped('car_id').filtered(lambda car: not car.active and not car.license_plate)
        vehicle_contracts = cars.with_context(active_test=False).mapped('log_contracts').filtered(
            lambda contract: not contract.active)
        return res + [cars, vehicle_contracts]

    def _get_advantage_values_company_car_total_depreciated_cost(self, contract, advantages):
        has_car = advantages['fold_company_car_total_depreciated_cost']
        selected_car = advantages['select_company_car_total_depreciated_cost']
        if not has_car or not selected_car:
            return {
                'transport_mode_car': False,
                'new_car': False,
                'new_car_model_id': False,
                'car_id': False,
            }
        car, car_id = selected_car.split('-')
        new_car = car == 'new'
        if new_car:
            return {
                'transport_mode_car': True,
                'new_car': True,
                'new_car_model_id': int(car_id),
                'car_id': False,
            }
        return {
            'transport_mode_car': True,
            'new_car': False,
            'new_car_model_id': False,
            'car_id': int(car_id),
        }

    def _get_advantage_values_company_bike_depreciated_cost(self, contract, advantages):
        has_bike = advantages['fold_company_bike_depreciated_cost']
        if not has_bike:
            return {
                'transport_mode_bike': False,
                'new_bike_model_id': False,
                'bike_id': False,
            }
        bike, bike_id = advantages['select_company_bike_depreciated_cost'].split('-')
        new_bike = bike == 'new'
        if new_bike:
            return {
                'transport_mode_bike': True,
                'new_bike_model_id': int(bike_id),
                'bike_id': False,
            }
        return {
            'transport_mode_bike': True,
            'new_bike_model_id': False,
            'bike_id': int(bike_id),
        }

    def _get_advantage_values_wishlist_car_total_depreciated_cost(self, contract, advantages):
        return {}

    def _get_description_company_car_total_depreciated_cost(self, new_value=None):
        advantage = self.env.ref('l10n_be_hr_contract_salary.l10n_be_transport_company_car')
        description = advantage.description
        if new_value is None or not new_value:
            if self.car_id:
                new_value = 'old-%s' % self.car_id.id
            elif self.new_car_model_id:
                new_value = 'new-%s' % self.new_car_model_id.id
            else:
                return description
        car_option, vehicle_id = new_value.split('-')
        try:
            vehicle_id = int(vehicle_id)
        except:
            return description
        if car_option == "new":
            vehicle = self.env['fleet.vehicle.model'].sudo().browse(vehicle_id)
            co2 = vehicle.default_co2
            fuel_type = vehicle.default_fuel_type
            door_number = odometer = immatriculation = False
        else:
            vehicle = self.env['fleet.vehicle'].sudo().browse(vehicle_id)
            co2 = vehicle.co2
            fuel_type = vehicle.fuel_type
            door_number = vehicle.doors
            odometer = vehicle.odometer
            immatriculation = vehicle.acquisition_date
        car_elements = {
            'CO2 Emission': co2,
            'Fuel Type': fuel_type,
            'Doors Number': door_number,
            'Odometer': odometer,
            'Immatriculation Date': immatriculation
        }
        description += '<ul>%s</ul>' % ''.join(['<li>%s: %s</li>' % (key, value) for key, value in car_elements.items() if value])
        return description

    def _get_description_commission_on_target(self, new_value=None):
        self.ensure_one()
        return '<span class="form-text">The commission is scalable and starts from the 1st € sold. The commission plan has stages with accelerators. At 100%%, 3 months are paid in Warrant which results to a monthly NET commission value of %s € and 9 months in cash which result in a GROSS monthly commission of %s €, taxable like your usual monthly pay.</span>' % (round(self.warrant_value_employee, 2), round(self.commission_on_target, 2))

    def _get_advantage_values_ip_value(self, contract, advantages):
        if not advantages['ip_value'] or not ast.literal_eval(advantages['ip_value']):
            return {
                'ip': False,
                'ip_wage_rate': contract.ip_wage_rate
            }
        return {
            'ip': True,
            'ip_wage_rate': contract.ip_wage_rate
        }
