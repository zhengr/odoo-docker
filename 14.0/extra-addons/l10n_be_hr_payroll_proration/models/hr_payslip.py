#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, models, fields, _
from pytz import timezone


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    meal_voucher_count = fields.Integer(
        compute='_compute_work_entry_dependent_benefits')  # Overrides compute method
    private_car_missing_days = fields.Integer(
        string='Days Not Granting Private Car Reimbursement',
        compute='_compute_work_entry_dependent_benefits')
    representation_fees_missing_days = fields.Integer(
        string='Days Not Granting Representation Fees',
        compute='_compute_work_entry_dependent_benefits')

    def _compute_work_entry_dependent_benefits(self):
        if self.env.context.get('salary_simulation'):
            for payslip in self:
                payslip.meal_voucher_count = 20
                payslip.private_car_missing_days = 0
                payslip.representation_fees_missing_days = 0
        else:
            work_entries_benefits_rights = self.env['l10n_be.work.entry.daily.benefit.report'].search([
                ('employee_id', 'in', self.mapped('employee_id').ids),
                ('day', '<=', max(self.mapped('date_to'))),
                ('day', '>=', min(self.mapped('date_from')))])

            for payslip in self:

                contract = payslip.contract_id
                benefits = {benefit: 0 for benefit in self.env['hr.work.entry.type'].get_work_entry_type_benefits()}

                date_from = max(payslip.date_from, contract.date_start)
                date_to = min(payslip.date_to, contract.date_end or payslip.date_to)

                for work_entries_benefits_right in (
                        work_entries_benefits_right for work_entries_benefits_right in work_entries_benefits_rights
                        if date_from <= work_entries_benefits_right.day <= date_to and
                           payslip.employee_id == work_entries_benefits_right.employee_id):
                    if work_entries_benefits_right.benefit_name not in benefits:
                        benefits[work_entries_benefits_right.benefit_name] = 1
                    else:
                        benefits[work_entries_benefits_right.benefit_name] += 1

                calendar = contract.resource_calendar_id if not contract.time_credit else contract.standard_calendar_id

                tz = timezone(calendar.tz)
                resource = contract.employee_id.resource_id
                intervals = calendar._attendance_intervals_batch(
                    tz.localize(fields.Datetime.to_datetime(payslip.date_from)),
                    tz.localize(fields.Datetime.to_datetime(payslip.date_to) + timedelta(days=1, seconds=-1)),
                    resources=resource, tz=tz)
                nb_of_days_to_work = len({dt_from.date(): True for (dt_from, dt_to, attendance) in intervals[resource.id]})
                payslip.private_car_missing_days = nb_of_days_to_work - (benefits['private_car'] if 'private_car' in benefits else 0)
                payslip.representation_fees_missing_days = nb_of_days_to_work - (benefits['representation_fees'] if 'representation_fees' in benefits else 0)
                payslip.meal_voucher_count = benefits['meal_voucher']
