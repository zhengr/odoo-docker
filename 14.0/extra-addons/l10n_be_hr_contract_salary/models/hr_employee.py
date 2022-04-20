# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    id_card = fields.Binary(string="ID Card Copy", groups="hr_contract.group_hr_contract_manager")
    driving_license = fields.Binary(string="Driving License", groups="hr_contract.group_hr_contract_manager")
    mobile_invoice = fields.Binary(string="Mobile Subscription Invoice", groups="hr_contract.group_hr_contract_manager")
    sim_card = fields.Binary(string="SIM Card Copy", groups="hr_contract.group_hr_contract_manager")
    internet_invoice = fields.Binary(string="Internet Subscription Invoice", groups="hr_contract.group_hr_contract_manager")
