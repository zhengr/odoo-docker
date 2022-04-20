# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime


class HrContract(models.Model):
    _inherit = 'hr.contract'


    def _generate_work_entries(self, date_start, date_stop):
        if self.env.context.get('force_work_entry_generation'):
            date_start = fields.Datetime.to_datetime(date_start)
            date_stop = datetime.combine(fields.Datetime.to_datetime(date_stop), datetime.max.time())

            vals_list = []
            for contract in self:
                vals_list += contract._get_work_entries_values(date_start, date_stop)

            if not vals_list:
                return self.env['hr.work.entry']
            return self.env['hr.work.entry'].create(vals_list)
        return super()._generate_work_entries(date_start, date_stop)
