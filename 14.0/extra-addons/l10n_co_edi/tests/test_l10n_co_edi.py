# coding: utf-8
import os
import re
from unittest.mock import patch, Mock

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.tools import misc, mute_logger


@tagged('post_install', '-at_install')
class TestColumbianInvoice(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref='l10n_co.l10n_co_chart_template_generic'):
        super(TestColumbianInvoice, cls).setUpClass(chart_template_ref=chart_template_ref)

        cls.salesperson = cls.env.ref('base.user_admin')
        cls.salesperson.function = 'Sales'

        currency_cop = cls.env.ref('base.COP')

        report_text = 'GRANDES CONTRIBUYENTES SHD Res. DDI-042065 13-10-17'
        cls.company_data['company'].write({
            'country_id': cls.env.ref('base.co').id,
            'l10n_co_edi_header_gran_contribuyente': report_text,
            'l10n_co_edi_header_tipo_de_regimen': report_text,
            'l10n_co_edi_header_retenedores_de_iva': report_text,
            'l10n_co_edi_header_autorretenedores': report_text,
            'l10n_co_edi_header_resolucion_aplicable': report_text,
            'l10n_co_edi_header_actividad_economica': report_text,
            'l10n_co_edi_header_bank_information': report_text,
            'vat': '213123432-1',
            'phone': '+1 555 123 8069',
            'website': 'http://www.example.com',
            'email': 'info@yourcompany.example.com',
            'street': 'Route de Ramilies',
            'zip': '1234',
            'city': 'Bogota',
            'state_id': cls.env.ref('base.state_co_01').id,
        })

        cls.company_data['company'].partner_id.write({
            'l10n_latam_identification_type_id': cls.env.ref('l10n_co.rut'),
            'l10n_co_edi_representation_type_id': cls.env.ref('l10n_co_edi.representation_type_0').id,
            'l10n_co_edi_establishment_type_id': cls.env.ref('l10n_co_edi.establishment_type_0').id,
            'l10n_co_edi_obligation_type_ids': [(6, 0, [cls.env.ref('l10n_co_edi.obligation_type_1').id])],
            'l10n_co_edi_customs_type_ids': [(6, 0, [cls.env.ref('l10n_co_edi.customs_type_0').id])],
            'l10n_co_edi_large_taxpayer': True,
        })

        cls.company_data_2['company'].write({
            'country_id': cls.env.ref('base.co').id,
            'phone': '(870)-931-0505',
            'website': 'hhtp://wwww.company_2.com',
            'email': 'company_2@example.com',
            'street': 'Route de Eghezée',
            'zip': '4567',
            'city': 'Medellín',
            'state_id': cls.env.ref('base.state_co_02').id,
            'vat': '213.123.432-1',
        })

        cls.company_data_2['company'].partner_id.write({
            'l10n_latam_identification_type_id': cls.env.ref('l10n_co.rut'),
            'l10n_co_edi_representation_type_id': cls.env.ref('l10n_co_edi.representation_type_0').id,
            'l10n_co_edi_establishment_type_id': cls.env.ref('l10n_co_edi.establishment_type_0').id,
            'l10n_co_edi_obligation_type_ids': [(6, 0, [cls.env.ref('l10n_co_edi.obligation_type_1').id])],
            'l10n_co_edi_customs_type_ids': [(6, 0, [cls.env.ref('l10n_co_edi.customs_type_0').id])],
            'l10n_co_edi_large_taxpayer': True,
        })

        cls.product_a.default_code = 'P0000'

        cls.tax = cls.company_data['default_tax_sale']
        cls.tax.amount = 15
        cls.tax.l10n_co_edi_type = cls.env.ref('l10n_co_edi.tax_type_0')
        cls.retention_tax = cls.tax.copy({
            'l10n_co_edi_type': cls.env.ref('l10n_co_edi.tax_type_9').id
        })

        cls.account_revenue = cls.company_data['default_account_revenue']

        cls.env.ref('uom.product_uom_unit').l10n_co_edi_ubl = 'S7'

    def test_dont_handle_non_colombian(self):
        self.company_data['company'].country_id = self.env.ref('base.us')
        product = self.product_a
        invoice = self.env['account.move'].with_context(default_move_type='out_invoice').create({
            'partner_id': self.company_data_2['company'].partner_id.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': product.id,
                    'quantity': 1,
                    'price_unit': 42,
                    'name': 'something',
                })
            ]
        })

        invoice.action_post()
        self.assertEqual(invoice.l10n_co_edi_invoice_status, 'not_sent',
                         'Invoices belonging to a non-Colombian company should not be sent.')

    def _validate_and_compare(self, invoice, invoice_name, filename_expected):

        return_value = {
            'message': 'mocked success',
            'transactionId': 'mocked_success',
        }
        with patch('odoo.addons.l10n_co_edi.models.carvajal_request.CarvajalRequest.upload', new=Mock(return_value=return_value)):
            with patch('odoo.addons.l10n_co_edi.models.carvajal_request.CarvajalRequest._init_client', new=Mock(return_value=None)):
                invoice.action_post()

        invoice.name = invoice_name
        generated_xml = invoice._l10n_co_edi_generate_xml().decode()

        # the ENC_{7,8,16} tags contain information related to the "current" date
        for date_tag in ('ENC_7', 'ENC_8', 'ENC_16'):
            generated_xml = re.sub('<%s>.*</%s>' % (date_tag, date_tag), '', generated_xml)

        # show the full diff
        self.maxDiff = None
        with misc.file_open(os.path.join('l10n_co_edi', 'tests', filename_expected)) as f:
            self.assertEqual(f.read().strip(), generated_xml.strip())

    def test_invoice(self):
        '''Tests if we generate an accepted XML for an invoice and a credit note.'''

        # l10n_co_edi_ubl_2_1 override a few methods from l10n_co_edi and shaddows the generation of the XML.
        # TODO refactor l10n_co_edi_ubl_2_1 to make it possible to export in both format or delete ubl 2.0 completely.
        if self.env['ir.module.module'].search([('name', '=', 'l10n_co_edi_ubl_2_1'), ('state', '=', 'installed')], limit=1):
            self.skipTest("l10n_co_edi_ubl_2_1 shadows features that this test tests")

        product = self.product_a
        invoice = self.env['account.move'].create({
            'partner_id': self.company_data_2['company'].partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': '2020-08-31',
            'invoice_user_id': self.salesperson.id,
            'name': 'OC 123',
            'invoice_payment_term_id': self.env.ref('account.account_payment_term_end_following_month').id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': product.id,
                    'quantity': 150,
                    'price_unit': 250,
                    'discount': 10,
                    'name': 'Line 1',
                    'tax_ids': [(6, 0, (self.tax.id, self.retention_tax.id))],
                }),
                (0, 0, {
                    'product_id': product.id,
                    'quantity': 1,
                    'price_unit': 0.2,
                    'name': 'Line 2',
                    'tax_ids': [(6, 0, (self.tax.id, self.retention_tax.id))],
                    'product_uom_id': self.env.ref('uom.product_uom_unit').id,
                })
            ]
        })

        self._validate_and_compare(invoice, 'TEST/00001', 'accepted_invoice.xml')

        # To stop a warning about "Tax Base Amount not computable
        # probably due to a change in an underlying tax " which seems
        # to be expected when generating refunds.
        with mute_logger('odoo.addons.account.models.account_invoice'):
            credit_note = invoice._reverse_moves([{'invoice_date': '2020-08-31'}])

        self._validate_and_compare(credit_note, 'TEST/00002', 'accepted_credit_note.xml')
