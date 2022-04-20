# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _should_bypass_set_qty_producing(self):
        production = self.raw_material_production_id or self.production_id
        if production and self.has_tracking == 'none' and ((self.product_id in production.workorder_ids.quality_point_ids.component_id) or self.operation_id):
            return True
        return super()._should_bypass_set_qty_producing()
