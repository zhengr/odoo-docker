# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.hr_contract_salary.controllers.main import HrContractSalary
from odoo.http import route, request
from odoo.tools.float_utils import float_compare


class HrContractSalary(HrContractSalary):

    def _get_compute_results(self, new_contract):
        result = super()._get_compute_results(new_contract)

        # generate a payslip corresponding to only this contract
        payslip = request.env['hr.payslip'].sudo().create({
            'employee_id': new_contract.employee_id.id,
            'contract_id': new_contract.id,
            'struct_id': new_contract.structure_type_id.default_struct_id.id,
            'company_id': new_contract.employee_id.company_id.id,
            'name': 'Payslip Simulation',
            'date_from': request.env['hr.payslip'].default_get(['date_from'])['date_from'],
            'date_to': request.env['hr.payslip'].default_get(['date_to'])['date_to'],
        })

        payslip.with_context(salary_simulation=True, lang=None).compute_sheet()

        result['payslip_lines'] = [(
            line.name,
            abs(round(line.total, 2)),
            line.code,
            'no_sign' if line.code in ['BASIC', 'SALARY', 'GROSS', 'NET'] else float_compare(line.total, 0, precision_digits=2)
        ) for line in payslip.line_ids]
        resume_lines = request.env['hr.contract.salary.resume'].search([
            '|',
            ('structure_type_id', '=', False),
            ('structure_type_id', '=', new_contract.structure_type_id.id),
            ('value_type', 'in', ['payslip', 'monthly_total'])])
        monthly_total = 0
        monthly_total_lines = resume_lines.filtered(lambda l: l.value_type == 'monthly_total')

        for resume_line in resume_lines - monthly_total_lines:
            value = round(payslip._get_salary_line_total(resume_line.code), 2)
            result['resume_lines_mapped'][resume_line.category_id.name][resume_line.code] = (resume_line.name, value, new_contract.company_id.currency_id.symbol)
            if resume_line.impacts_monthly_total:
                monthly_total += value / 12.0 if resume_line.category_id.periodicity == 'yearly' else value

        for resume_line in monthly_total_lines:
            super_line = result['resume_lines_mapped'][resume_line.category_id.name][resume_line.code]
            new_value = (super_line[0], super_line[1] + round(float(monthly_total), 2), super_line[2])
            result['resume_lines_mapped'][resume_line.category_id.name][resume_line.code] = new_value
        return result
