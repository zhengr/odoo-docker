# -*- coding: utf-8 -*-
from odoo import models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def reconcile(self):
        # OVERRIDE
        # when a payment is renconciled, its transaction's status transitions from pending to done.
        # the post processing is called subsequently, it will confirm and invoice the sale order.
        res = super().reconcile()

        involved_payments = self.move_id.payment_id
        tx = self.env['payment.transaction'].search([
            ('state', '=', 'pending'),
            ('acquirer_id.provider', '=', 'sepa_direct_debit'),
            ('payment_id', 'in', involved_payments.filtered('is_matched').ids),
        ])
        tx._set_transaction_done()
        tx.execute_callback()
        tx._post_process_after_done()

        return res
