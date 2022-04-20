# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo.tools import float_compare, float_round


class Task(models.Model):
    _inherit = "project.task"

    def action_fsm_validate(self):
        result = super(Task, self).action_fsm_validate()

        for task in self:
            if task.allow_billable and task.sale_order_id:
                task.sudo()._validate_stock()
        return result

    def _validate_stock(self):
        self.ensure_one()
        all_fsm_sn_moves = self.env['stock.move']
        ml_to_create = []
        for so_line in self.sale_order_id.order_line:
            qty = so_line.product_uom_qty - so_line.qty_delivered
            fsm_sn_moves = self.env['stock.move']
            if not qty:
                continue
            for last_move in so_line.move_ids.filtered(lambda p: p.state not in ['done', 'cancel']):
                move = last_move
                fsm_sn_moves |= last_move
                while move.move_orig_ids:
                    move = move.move_orig_ids
                    fsm_sn_moves |= move
            for fsm_sn_move in fsm_sn_moves:
                ml_vals = fsm_sn_move._prepare_move_line_vals(quantity=0)
                ml_vals['qty_done'] = qty
                ml_vals['lot_id'] = so_line.fsm_lot_id.id
                ml_to_create.append(ml_vals)
            all_fsm_sn_moves |= fsm_sn_moves
        self.env['stock.move.line'].create(ml_to_create)

        pickings_to_do = self.sale_order_id.picking_ids.filtered(lambda p: p.state not in ['done', 'cancel'])
        # set the quantity done as the initial demand before validating the pickings
        for move in pickings_to_do.move_lines:
            if move.state in ('done', 'cancel') or move in all_fsm_sn_moves:
                continue
            rounding = move.product_uom.rounding
            if float_compare(move.quantity_done, move.product_uom_qty, precision_rounding=rounding) < 0:
                qty_to_do = float_round(
                    move.product_uom_qty - move.quantity_done,
                    precision_rounding=rounding,
                    rounding_method='HALF-UP')
                move._set_quantity_done(qty_to_do)
        pickings_to_do.with_context(skip_sms=True, cancel_backorder=True).button_validate()

    def write(self, vals):
        result = super().write(vals)
        if 'user_id' in vals:
            orders = self.mapped('sale_order_id').filtered(lambda order: order.state in ['draft', 'sent'])
            orders.write({'user_id': vals['user_id']})
        return result
