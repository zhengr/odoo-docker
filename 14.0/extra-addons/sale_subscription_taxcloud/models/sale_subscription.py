# -*- coding: utf-8 -*-

from odoo import models

class SaleSubscription(models.Model):
    """Ensure a correct invoice by validating taxcloud taxes in the subscription before invoice generation."""
    _inherit = "sale.subscription"


def _do_payment(self, payment_token, invoice, two_steps_sec=True):
    if invoice.fiscal_position_id.is_taxcloud and invoice.type in ["out_invoice", "out_refund"]:
        invoice.with_context(taxcloud_authorize_transaction=True).validate_taxes_on_invoice()
    return super(SaleSubscription, self)._do_payment(payment_token, invoice, two_steps_sec=two_steps_sec)
