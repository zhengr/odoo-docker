# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.models import MAGIC_COLUMNS
from odoo.fields import Date
from odoo.exceptions import ValidationError
from odoo.tools import html_sanitize

_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    # YTI TODO: Introduce a country_code field to hide country specific advantages fields
    origin_contract_id = fields.Many2one('hr.contract', string="Origin Contract", domain="[('company_id', '=', company_id)]", help="The contract from which this contract has been duplicated.")
    is_origin_contract_template = fields.Boolean(compute='_compute_is_origin_contract_template', string='Is origin contract a contract template ?', readonly=True)
    hash_token = fields.Char('Created From Token', copy=False)
    applicant_id = fields.Many2one('hr.applicant', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    contract_reviews_count = fields.Integer(compute="_compute_contract_reviews_count", string="Proposed Contracts Count")
    # Should be moved to l10n_be_hr_contract_salary
    contract_type = fields.Selection([
        ('PFI', 'PFI'),
        ('CDI', 'CDI'),
        ('CDD', 'CDD')], string="Contract Type", default="PFI")
    default_contract_id = fields.Many2one('hr.contract', string="Contract Template",
        domain="[('company_id', '=', company_id)]",
        help="Default contract used when making an offer to an applicant.")
    sign_template_id = fields.Many2one('sign.template', string="New Contract Document Template",
        help="Default document that the applicant will have to sign to accept a contract offer.")
    contract_update_template_id = fields.Many2one('sign.template', string="Contract Update Document Template",
        help="Default document that the employee will have to sign to update his contract.")
    signatures_count = fields.Integer(compute='_compute_signatures_count', string='# Signatures',
        help="The number of signatures on the pdf contract with the most signatures.")
    image_1920 = fields.Image(related='employee_id.image_1920', groups="hr_contract.group_hr_contract_manager")
    # YTI FIXME: holidays and wage_with_holidays are defined twice...
    holidays = fields.Float(string='Paid Time Off',
        help="Number of days of paid leaves the employee gets per year.")
    wage_with_holidays = fields.Monetary(compute='_compute_wage_with_holidays', inverse='_inverse_wage_with_holidays',
        tracking=True, string="Wage update with holidays retenues")

    # Employer costs fields
    final_yearly_costs = fields.Monetary(compute='_compute_final_yearly_costs',
        readonly=False, store=True,
        string="Employee Budget",
        tracking=True,
        help="Total yearly cost of the employee for the employer.")
    monthly_yearly_costs = fields.Monetary(compute='_compute_monthly_yearly_costs', string='Monthly Equivalent Cost', readonly=True,
        help="Total monthly cost of the employee for the employer.")

    @api.depends('origin_contract_id')
    def _compute_is_origin_contract_template(self):
        for contract in self:
            contract.is_origin_contract_template = contract.origin_contract_id and not contract.origin_contract_id.employee_id

    @api.depends('holidays', 'wage', 'final_yearly_costs')
    def _compute_wage_with_holidays(self):
        for contract in self:
            if contract.holidays:
                yearly_cost = contract.final_yearly_costs * (1.0 - contract.holidays / 231.0)
                contract.wage_with_holidays = contract._get_gross_from_employer_costs(yearly_cost)
            else:
                contract.wage_with_holidays = contract.wage

    def _inverse_wage_with_holidays(self):
        for contract in self:
            if contract.holidays:
                yearly_cost = contract._get_advantages_costs() + contract._get_salary_costs_factor() * contract.wage_with_holidays
                # YTI TODO: The number of working days per year could be a setting on the company
                contract.final_yearly_costs = yearly_cost / (1.0 - contract.holidays / 231.0)
                contract.wage = contract._get_gross_from_employer_costs(contract.final_yearly_costs)
            else:
                contract.wage = contract.wage_with_holidays

    def _get_advantage_description(self, advantage, new_value=None):
        self.ensure_one()
        if hasattr(self, '_get_description_%s' % advantage.field):
            description = getattr(self, '_get_description_%s' % advantage.field)(new_value)
        else:
            description = advantage.description
        return html_sanitize(description)

    def _get_advantage_fields(self):
        types = ('float', 'integer', 'monetary', 'boolean')
        fields = set(field.name for field in self._fields.values() if field.type in types)
        return tuple(fields - self._advantage_black_list())

    @api.model
    def _advantage_black_list(self):
        return set(MAGIC_COLUMNS + ["wage_with_holidays"])

    @api.depends(lambda self: (
        'structure_type_id.salary_advantage_ids.res_field_id',
        'structure_type_id.salary_advantage_ids.impacts_net_salary',
        *self._get_advantage_fields()))
    def _compute_final_yearly_costs(self):
        for contract in self:
            contract.final_yearly_costs = contract._get_advantages_costs() + contract._get_salary_costs_factor() * contract.wage

    @api.onchange("wage_with_holidays")
    def _onchange_wage_with_holidays(self):
        self._inverse_wage_with_holidays()

    @api.onchange('final_yearly_costs')
    def _onchange_final_yearly_costs(self):
        self.wage = self._get_gross_from_employer_costs(self.final_yearly_costs)

    @api.depends('final_yearly_costs')
    def _compute_monthly_yearly_costs(self):
        for contract in self:
            contract.monthly_yearly_costs = contract.final_yearly_costs / 12.0

    def _get_salary_costs_factor(self):
        self.ensure_one()
        return 12.0

    def _get_advantages_costs(self):
        self.ensure_one()
        advantages = self.env['hr.contract.salary.advantage'].search([
            ('impacts_net_salary', '=', True),
            ('structure_type_id', '=', self.structure_type_id.id),
            ('cost_field', '!=', False),
        ])
        if not advantages:
            return 0
        monthly_advantages = advantages.filtered(lambda a: a.advantage_type_id.periodicity == 'monthly')
        monthly_cost = sum(self[advantage.cost_field] if advantage.cost_field in self else 0 for advantage in monthly_advantages)
        yearly_cost = sum(self[advantage.cost_field] if advantage.cost_field in self else 0 for advantage in advantages - monthly_advantages)
        return monthly_cost * 12 + yearly_cost

    def _get_gross_from_employer_costs(self, yearly_cost):
        self.ensure_one()
        remaining_for_gross = yearly_cost - self._get_advantages_costs()
        return remaining_for_gross / self._get_salary_costs_factor()

    @api.depends('sign_request_ids.nb_closed')
    def _compute_signatures_count(self):
        for contract in self:
            contract.signatures_count = max(contract.sign_request_ids.mapped('nb_closed') or [0])

    @api.depends('origin_contract_id')
    def _compute_contract_reviews_count(self):
        for contract in self:
            contract.contract_reviews_count = self.with_context(active_test=False).search_count(
                [('origin_contract_id', '=', contract.id)])

    def _get_redundant_salary_data(self):
        employees = self.mapped('employee_id').filtered(lambda employee: not employee.active)
        partners = employees.mapped('address_home_id').filtered(
            lambda partner: not partner.active and partner.type == 'private')
        return [employees, partners]

    def _clean_redundant_salary_data(self):
        # Unlink archived draft contract older than 7 days linked to a signature
        # Unlink the related employee, partner, and new car (if any)
        seven_days_ago = date.today() + relativedelta(days=-7)
        contracts = self.search([
            ('state', '=', 'draft'),
            ('active', '=', False),
            ('sign_request_ids', '!=', False),
            ('create_date', '<=', Date.to_string(seven_days_ago))])
        records_to_unlink = contracts._get_redundant_salary_data()
        for records in records_to_unlink:
            if not records:
                continue
            _logger.info('Salary: About to unlink %s: %s' % (records._name, records.ids))
            for record in records:
                try:
                    record.unlink()
                except ValueError:
                    pass

    def action_show_contract_reviews(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.contract",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [["origin_contract_id", "=", self.id], '|', ["active", "=", False], ["active", "=", True]],
            "name": "Contracts Reviews",
        }

    def action_view_origin_contract(self):
        action = self.env["ir.actions.actions"]._for_xml_id("hr_contract.action_hr_contract")
        action['views'] = [(self.env.ref('hr_contract.hr_contract_view_form').id, 'form')]
        action['res_id'] = self.origin_contract_id.id
        return action

    def send_offer(self):
        self.ensure_one()
        if self.employee_id.address_home_id:
            try:
                template_id = self.env.ref('hr_contract_salary.mail_template_send_offer').id
            except ValueError:
                template_id = False
            try:
                compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
            except ValueError:
                compose_form_id = False
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            path = '/salary_package/contract/' + str(self.id)
            ctx = {
                'default_model': 'hr.contract',
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'salary_package_url': base_url + path,
                'custom_layout': 'mail.mail_notification_light'
            }
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
                'context': ctx,
            }
        else:
            raise ValidationError(_("No private address defined on the employee!"))
