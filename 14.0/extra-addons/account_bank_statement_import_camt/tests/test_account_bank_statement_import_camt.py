# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.exceptions import UserError
from odoo.modules.module import get_module_resource
from odoo.addons.account_bank_statement_import_camt.wizard.account_bank_statement_import_camt import _logger as camt_wizard_logger

import base64


@tagged('post_install', '-at_install')
class TestAccountBankStatementImportCamt(AccountTestInvoicingCommon):

    def test_camt_file_import(self):
        bank_journal = self.env['account.journal'].create({
            'name': 'Bank 123456',
            'code': 'BNK67',
            'type': 'bank',
            'bank_acc_number': '123456',
            'currency_id': self.env.ref('base.USD').id,
        })

        partner_norbert = self.env['res.partner'].create({
            'name': 'Norbert Brant',
            'is_company': True,
        })
        bank_norbert = self.env['res.bank'].create({'name': 'test'})

        self.env['res.partner.bank'].create({
            'acc_number': 'BE93999574162167',
            'partner_id': partner_norbert.id,
            'bank_id': bank_norbert.id,
        })

        # Get CAMT file content
        camt_file_path = get_module_resource(
            'account_bank_statement_import_camt',
            'test_camt_file',
            'test_camt.xml',
        )
        camt_file = base64.b64encode(open(camt_file_path, 'rb').read())

        # Use an import wizard to process the file
        self.env['account.bank.statement.import']\
            .with_context(journal_id=bank_journal.id)\
            .create({'attachment_ids': [(0, 0, {'name': 'test file', 'datas': camt_file})]})\
            .import_file()

        # Check the imported bank statement
        imported_statement = self.env['account.bank.statement'].search([('company_id', '=', self.env.company.id)])
        self.assertRecordValues(imported_statement, [{
            'name': '0574908765.2015-12-05',
            'balance_start': 8998.20,
            'balance_end_real': 2661.49,
        }])
        self.assertRecordValues(imported_statement.line_ids.sorted('ref'), [
            {
                'ref': 'INNDNL2U20141231000142300002844',
                'partner_name': 'ASUSTeK',
                'amount': -7379.54,
                'partner_id': False,
            },
            {
                'ref': 'INNDNL2U20150105000217200000708',
                'partner_name': partner_norbert.name,
                'amount': 1636.88,
                'partner_id': partner_norbert.id,
            },
            {
                'ref': 'TESTBANK/NL/20151129/01206408',
                'partner_name': 'China Export',
                'amount': -564.05,
                'partner_id': False,
            },
        ])

    def test_minimal_camt_file_import(self):
        # Create a bank account and journal corresponding to the CAMT
        # file (same currency and account number)
        bank_journal = self.env['account.journal'].create({
            'name': "Bank 112233",
            'code': 'BNK68',
            'type': 'bank',
            'bank_acc_number': '112233',
            'currency_id': self.env.ref('base.USD').id,
        })

        # Use an import wizard to process the file
        camt_file_path = get_module_resource(
            'account_bank_statement_import_camt',
            'test_camt_file',
            'camt_053_minimal.xml',
        )
        camt_file = base64.b64encode(open(camt_file_path, 'rb').read())

        self.env['account.bank.statement.import']\
            .with_context(journal_id=bank_journal.id)\
            .create({'attachment_ids': [(0, 0, {'name': 'test file', 'datas': camt_file})]})\
            .import_file()

        # Check the imported bank statement
        imported_statement = self.env['account.bank.statement'].search([('company_id', '=', self.env.company.id)])
        self.assertRecordValues(imported_statement, [{
            'name': '2514988305.2019-02-13',
            'balance_start': 1000.00,
            'balance_end_real': 1500.00,
        }])
        self.assertRecordValues(imported_statement.line_ids.sorted('ref'), [{'amount': 500.00}])

    def test_several_ibans_match_journal_camt_file_import(self):
        # Create a bank account and journal corresponding to the CAMT
        # file (same currency and account number)
        bank_journal = self.env['account.journal'].create({
            'name': "Bank BE86 6635 9439 7150",
            'code': 'BNK69',
            'type': 'bank',
            'bank_acc_number': 'BE86 6635 9439 7150',
            'currency_id': self.env.ref('base.USD').id,
        })

        # Use an import wizard to process the file
        camt_file_path = get_module_resource(
            'account_bank_statement_import_camt',
            'test_camt_file',
            'camt_053_several_ibans.xml',
        )
        camt_file = base64.b64encode(open(camt_file_path, 'rb').read())

        wizard = self.env['account.bank.statement.import']\
            .with_context(journal_id=bank_journal.id)\
            .create({'attachment_ids': [(0, 0, {'name': 'test file', 'datas': camt_file})]})

        with self.assertLogs(level="WARNING") as log_catcher:
            wizard.import_file()
        self.assertEqual(len(log_catcher.output), 1, "Exactly one warning should be logged")
        self.assertIn(
            "The following statements will not be imported",
            log_catcher.output[0],
            "The logged warning warns about non-imported statements",
        )

        # Check the imported bank statement
        imported_statement = self.env['account.bank.statement'].search([('company_id', '=', self.env.company.id)])
        self.assertRecordValues(imported_statement, [{
            'name': '2514988305.2019-05-23',
            'balance_start': 1000.00,
            'balance_end_real': 1600.00,
        }])
        self.assertRecordValues(imported_statement.line_ids.sorted('ref'), [{'amount': 600.00}])

    def test_several_ibans_missing_journal_id_camt_file_import(self):
        # Create a bank account and journal corresponding to the CAMT
        # file (same currency and account number)
        bank_journal = self.env['account.journal'].create({
            'name': "Bank BE43 9787 8497 9701",
            'code': 'BNK69',
            'type': 'bank',
            'currency_id': self.env.ref('base.USD').id,
            # missing bank account number
        })

        # Use an import wizard to process the file
        camt_file_path = get_module_resource(
            'account_bank_statement_import_camt',
            'test_camt_file',
            'camt_053_several_ibans.xml',
        )
        camt_file = base64.b64encode(open(camt_file_path, 'rb').read())

        wizard = self.env['account.bank.statement.import']\
            .with_context(journal_id=bank_journal.id)\
            .create({'attachment_ids': [(0, 0, {'name': 'test file', 'datas': camt_file})]})

        with self.assertLogs(camt_wizard_logger, level="WARNING") as log_catcher:
            with self.assertRaises(UserError) as error_catcher:
                wizard.import_file()

        self.assertEqual(len(log_catcher.output), 1, "Exactly one warning should be logged")
        self.assertIn(
            "The following statements will not be imported",
            log_catcher.output[0],
            "The logged warning warns about non-imported statements",
        )

        self.assertEqual(error_catcher.exception.args[0], (
            "Please set the IBAN account on your bank journal.\n\n"
            "This CAMT file is targeting several IBAN accounts but none match the current journal."
        ))
