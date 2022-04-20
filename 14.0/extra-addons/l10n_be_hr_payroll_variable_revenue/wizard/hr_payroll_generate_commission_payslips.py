# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import contextlib
import io
import base64

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import pycompat


class HrPayrollGenerateCommissionPayslips(models.TransientModel):
    _name = 'hr.payroll.generate.commission.payslips'
    _description = "Generate Commission Payslips"

    name = fields.Char()
    date_start = fields.Date(string='Date From', required=True,
        default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=-2, day=1)).date()))
    date_end = fields.Date(string='Date To', required=True,
        default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    line_ids = fields.One2many(
        'hr.payroll.generate.commission.payslips.line', 'wizard_id',
        compute="_compute_line_ids", store=True, readonly=False)
    commission_type = fields.Selection([
        ('commission', 'Classic Commission'),
        ('wrrant', 'Warrant'),
    ], required=True, default='commission')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('export', 'Export the employees file'),
        ('import', 'Import the employee file')], default='draft')
    import_file = fields.Binary('Import File', attachment=False)
    department_id = fields.Many2one('hr.department', domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")

    @api.depends('department_id')
    def _compute_line_ids(self):
        employees = self.env['hr.employee'].search([
            ('department_id', 'ilike', self.department_id.name),
            ('contract_ids.state', 'in', ('open', 'close')),
            ('company_id', '=', self.env.company.id)
        ])
        self.write({
            'line_ids': [(5, 0, 0)] + [(0, 0, {
                'employee_id': e.id,
                'commission_amount': e.contract_id.commission_on_target * 3
            }) for e in employees] if self.department_id else []
        })

    def _reopen_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payroll.generate.commission.payslips',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def export_employee_file(self):
        with contextlib.closing(io.BytesIO()) as buf:
            writer = pycompat.csv_writer(buf, quoting=1)
            writer.writerow(("Employee Name", "ID", "Commission on Target"))

            for line in self.line_ids:
                writer.writerow((line.employee_id.name, str(line.employee_id.id), str(line.commission_amount)))
            content = buf.getvalue()

        name = "exported_employees.csv"
        self.write({'state': 'export', 'name': name})
        return content

    def import_employee_file(self):
        if not self.import_file:
            raise UserError(_('You should upload a file to import first.'))
        try:
            values = [(5, 0, 0)]
            for line in base64.decodebytes(self.import_file).decode('utf-8').split('\r\n')[1:]:
                line = line.split(',')
                if len(line) != 3:
                    continue
                values.append((0, 0, {
                    'employee_id': int(line[1].strip('"')),
                    'commission_amount': float(line[2].strip('"')),
                }))
            self.write({'line_ids': values, 'state': 'import'})
        except:
            raise UserError(_('Error while importing file'))
        return self._reopen_wizard()

    def generate_commission_payslips(self):
        batch = self.env["hr.payslip.run"].create({
            'name': 'Commissions : %s - %s' % (self.date_start, self.date_end),
            'state': 'draft',
            'date_start': self.date_start,
            'date_end': self.date_end,
        })
        mapped_commission_values = {
            line.employee_id.id: line.commission_amount for line in self.line_ids}

        if self.commission_type == 'commission':
            structure_id = self.env.ref('l10n_be_hr_payroll_variable_revenue.hr_payroll_structure_cp200_structure_commission').id
        else:
            structure_id = self.env.ref('l10n_be_hr_payroll.hr_payroll_structure_cp200_structure_warrant').id

        action_open_batch = self.env['hr.payslip.employees'].with_context(
            active_id=batch.id, commission_real_values=mapped_commission_values
        ).create({
            'employee_ids': self.line_ids.mapped('employee_id').ids,
            'structure_id': structure_id,
        }).compute_sheet()

        if not batch.slip_ids:
            raise UserError(_('There is no payslip to generate for those employees'))

        return action_open_batch

class HrPayrollGenerateCommissionPayslipsLine(models.TransientModel):
    _name = 'hr.payroll.generate.commission.payslips.line'
    _description = "Generate Commission Payslips Lines"

    wizard_id = fields.Many2one('hr.payroll.generate.commission.payslips')
    employee_id = fields.Many2one('hr.employee', required=True)
    commission_amount = fields.Monetary()
    currency_id = fields.Many2one('res.currency', related='wizard_id.currency_id')
