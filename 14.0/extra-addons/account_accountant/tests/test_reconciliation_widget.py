import logging
import odoo.tests
import time
from odoo.addons.account.tests.common import TestAccountReconciliationCommon

_logger = logging.getLogger(__name__)


@odoo.tests.tagged('post_install', '-at_install')
class TestReconciliationWidget(TestAccountReconciliationCommon):

    def test_statement_suggestion_other_currency(self):
        # company currency is EUR
        # payment in USD
        invoice = self.create_invoice(invoice_amount=50, currency_id=self.currency_usd_id)

        # journal currency in USD
        bank_stmt = self.env['account.bank.statement'].create({
            'journal_id': self.bank_journal_usd.id,
            'date': time.strftime('%Y-07-15'),
            'name': 'payment %s' % invoice.name,
            'line_ids': [(0, 0, {
                'payment_ref': 'payment',
                'partner_id': self.partner_agrolait_id,
                'amount': 50,
                'date': time.strftime('%Y-07-15'),
            })],
        })

        bank_stmt.button_post()

        result = self.env['account.reconciliation.widget'].get_bank_statement_line_data(bank_stmt.line_ids.ids)
        self.assertEqual(result['lines'][0]['reconciliation_proposition'][0]['amount_str'], '$ 50.00')

    def test_filter_partner1(self):
        inv1 = self.create_invoice(currency_id=self.currency_euro_id)
        inv2 = self.create_invoice(currency_id=self.currency_euro_id)
        partner = inv1.partner_id

        receivable1 = inv1.line_ids.filtered(lambda l: l.account_id.internal_type == 'receivable')
        receivable2 = inv2.line_ids.filtered(lambda l: l.account_id.internal_type == 'receivable')

        bank_stmt = self.env['account.bank.statement'].create({
            'company_id': self.company.id,
            'journal_id': self.bank_journal_euro.id,
            'date': time.strftime('%Y-07-15'),
            'name': 'test',
        })

        bank_stmt_line = self.env['account.bank.statement.line'].create({
            'payment_ref': 'testLine',
            'statement_id': bank_stmt.id,
            'amount': 100,
            'date': time.strftime('%Y-07-15'),
        })

        # This is like input a partner in the widget
        mv_lines_rec = self.env['account.reconciliation.widget'].get_move_lines_for_bank_statement_line(
            bank_stmt_line.id,
            partner_id=partner.id,
            excluded_ids=[],
            search_str=False,
            mode="rp",
        )
        mv_lines_ids = [l['id'] for l in mv_lines_rec]

        self.assertIn(receivable1.id, mv_lines_ids)
        self.assertIn(receivable2.id, mv_lines_ids)

        # With a partner set, type the invoice reference in the filter
        mv_lines_rec = self.env['account.reconciliation.widget'].get_move_lines_for_bank_statement_line(
            bank_stmt_line.id,
            partner_id=partner.id,
            excluded_ids=[],
            search_str=inv1.payment_reference,
            mode="rp",
        )
        mv_lines_ids = [l['id'] for l in mv_lines_rec]

        self.assertIn(receivable1.id, mv_lines_ids)
        self.assertNotIn(receivable2.id, mv_lines_ids)

        # Without a partner set, type "deco" in the filter
        mv_lines_rec = self.env['account.reconciliation.widget'].get_move_lines_for_bank_statement_line(
            bank_stmt_line.id,
            partner_id=False,
            excluded_ids=[],
            search_str="deco",
            mode="rp",
        )
        mv_lines_ids = [l['id'] for l in mv_lines_rec]

        self.assertIn(receivable1.id, mv_lines_ids)
        self.assertIn(receivable2.id, mv_lines_ids)

        # With a partner set, type "deco" in the filter and click on the first receivable
        mv_lines_rec = self.env['account.reconciliation.widget'].get_move_lines_for_bank_statement_line(
            bank_stmt_line.id,
            partner_id=partner.id,
            excluded_ids=[receivable1.id],
            search_str="deco",
            mode="rp",
        )
        mv_lines_ids = [l['id'] for l in mv_lines_rec]

        self.assertNotIn(receivable1.id, mv_lines_ids)
        self.assertIn(receivable2.id, mv_lines_ids)

    def test_partner_name_with_parent(self):
        parent_partner = self.env['res.partner'].create({
            'name': 'test',
        })
        child_partner = self.env['res.partner'].create({
            'name': 'test',
            'parent_id': parent_partner.id,
            'type': 'delivery',
        })
        self.create_invoice_partner(currency_id=self.currency_euro_id, partner_id=child_partner.id)

        bank_stmt = self.env['account.bank.statement'].create({
            'company_id': self.company.id,
            'journal_id': self.bank_journal_euro.id,
            'date': time.strftime('%Y-07-15'),
            'name': 'test',
        })

        bank_stmt_line = self.env['account.bank.statement.line'].create({
            'payment_ref': 'testLine',
            'statement_id': bank_stmt.id,
            'amount': 100,
            'date': time.strftime('%Y-07-15'),
            'partner_name': 'test',
        })

        bkstmt_data = self.env['account.reconciliation.widget'].get_bank_statement_line_data(bank_stmt_line.ids)

        self.assertEqual(len(bkstmt_data['lines']), 1)
        self.assertEqual(bkstmt_data['lines'][0]['partner_id'], parent_partner.id)

    def test_reconciliation_process_move_lines_with_mixed_currencies(self):
        # Delete any old rate - to make sure that we use the ones we need.
        old_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.currency_usd_id)])
        old_rates.unlink()

        self.env['res.currency.rate'].create({
            'currency_id': self.currency_usd_id,
            'name': time.strftime('%Y') + '-01-01',
            'rate': 2,
        })

        move_product = self.env['account.move'].create({
            'ref': 'move product',
        })
        move_product_lines = self.env['account.move.line'].create([
            {
                'name': 'line product',
                'move_id': move_product.id,
                'account_id': self.env['account.account'].search([
                    ('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id),
                    ('company_id', '=', self.company.id)
                ], limit=1).id,
                'debit': 20,
                'credit': 0,
            },
            {
                'name': 'line receivable',
                'move_id': move_product.id,
                'account_id': self.account_rcv.id,
                'debit': 0,
                'credit': 20,
            }
        ])
        move_product.action_post()

        move_payment = self.env['account.move'].create({
            'ref': 'move payment',
        })
        liquidity_account = self.env['account.account'].search([
            ('user_type_id', '=', self.env.ref('account.data_account_type_liquidity').id),
            ('company_id', '=', self.company.id)], limit=1)
        move_payment_lines = self.env['account.move.line'].create([
            {
                'name': 'line product',
                'move_id': move_payment.id,
                'account_id': liquidity_account.id,
                'debit': 10.0,
                'credit': 0,
                'amount_currency': 20,
                'currency_id': self.currency_usd_id,
            },
            {
                'name': 'line product',
                'move_id': move_payment.id,
                'account_id': self.account_rcv.id,
                'debit': 0,
                'credit': 10.0,
                'amount_currency': -20,
                'currency_id': self.currency_usd_id,
            }
        ])
        move_payment.action_post()

        # We are reconciling a move line in currency A with a move line in currency B and putting
        # the rest in a writeoff, this test ensure that the debit/credit value of the writeoff is
        # correctly computed in company currency.
        self.env['account.reconciliation.widget'].process_move_lines([{
            'id': False,
            'type': False,
            'mv_line_ids': [move_payment_lines[1].id, move_product_lines[1].id],
            'new_mv_line_dicts': [{
                'account_id': liquidity_account.id,
                'analytic_tag_ids': [(6, None, [])],
                'credit': 0,
                'date': time.strftime('%Y') + '-01-01',
                'debit': 15.0,
                'journal_id': self.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', self.company.id)], limit=1).id,
                'name': 'writeoff',
            }],
        }])

        writeoff_line = self.env['account.move.line'].search([('name', '=', 'writeoff'), ('company_id', '=', self.company.id)])
        self.assertEqual(writeoff_line.credit, 15.0)

    def test_inv_refund_foreign_payment_writeoff_domestic(self):
        company = self.company
        self.env['res.currency.rate'].search([]).unlink()
        self.env['res.currency.rate'].create({
            'name': time.strftime('%Y') + '-07-01',
            'rate': 1.0,
            'currency_id': self.currency_euro_id,
            'company_id': company.id
        })
        self.env['res.currency.rate'].create({
            'name': time.strftime('%Y') + '-07-01',
            'rate': 1.113900,  # Don't change this !
            'currency_id': self.currency_usd_id,
            'company_id': self.company.id
        })
        inv1 = self.create_invoice(invoice_amount=480, currency_id=self.currency_usd_id)
        inv2 = self.create_invoice(type="out_refund", invoice_amount=140, currency_id=self.currency_usd_id)

        payment = self.env['account.payment'].create({
            'payment_method_id': self.inbound_payment_method.id,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': inv1.partner_id.id,
            'amount': 287.20,
            'journal_id': self.bank_journal_euro.id,
            'company_id': company.id,
        })
        payment.action_post()

        inv1_receivable = inv1.line_ids.filtered(lambda l: l.account_id.internal_type == 'receivable')
        inv2_receivable = inv2.line_ids.filtered(lambda l: l.account_id.internal_type == 'receivable')
        pay_receivable = payment.line_ids.filtered(lambda l: l.account_id.internal_type == 'receivable')

        data_for_reconciliation = [
            {
                'type': 'partner',
                'id': inv1.partner_id.id,
                'mv_line_ids': (inv1_receivable + inv2_receivable + pay_receivable).ids,
                'new_mv_line_dicts': [
                    {
                        'credit': 18.04,
                        'debit': 0.00,
                        'journal_id': self.bank_journal_euro.id,
                        'name': 'Total WriteOff (Fees)',
                        'account_id': self.diff_expense_account.id
                    }
                ]
            }
        ]

        self.env["account.reconciliation.widget"].process_move_lines(data_for_reconciliation)

        self.assertTrue(inv1_receivable.full_reconcile_id.exists())
        self.assertEqual(inv1_receivable.full_reconcile_id, inv2_receivable.full_reconcile_id)
        self.assertEqual(inv1_receivable.full_reconcile_id, pay_receivable.full_reconcile_id)

        self.assertTrue(all(l.reconciled for l in inv1_receivable))
        self.assertTrue(all(l.reconciled for l in inv2_receivable))

        self.assertEqual(inv1.payment_state, 'in_payment')
        self.assertEqual(inv2.payment_state, 'paid')
