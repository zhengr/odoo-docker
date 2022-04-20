# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    check_ids = fields.One2many('quality.check', 'production_id', string="Checks")

    def action_assign(self):
        res = super().action_assign()
        for production in self:
            for workorder in production.workorder_ids:
                for check in workorder.check_ids:
                    if check.test_type not in ('register_consumed_materials', 'register_byproducts'):
                        continue
                    if check.move_line_id:
                        continue
                    check.write(workorder._defaults_from_move(check.move_id))
        return res

    def _generate_backorder_productions(self, close_mo=True):
        backorders = super()._generate_backorder_productions(close_mo=close_mo)
        for wo in backorders.workorder_ids:
            if wo.component_id:
                wo._update_component_quantity()
        return backorders

    def _button_mark_done_sanity_checks(self):
        checks_not_process = self.workorder_ids.check_ids.filtered(lambda c: c.quality_state == 'none' and c.test_type not in ('register_consumed_materials', 'register_byproducts'))
        if checks_not_process:
            error_msg = _('Please go in the Operations tab and perform the following work orders and their quality checks:\n')
            for check in checks_not_process:
                error_msg += check.workorder_id.workcenter_id.name + ' - ' + check.name
                if check.title:
                    error_msg += ' - ' + check.title
                error_msg += '\n'
            raise UserError(error_msg)
        return super()._button_mark_done_sanity_checks()
