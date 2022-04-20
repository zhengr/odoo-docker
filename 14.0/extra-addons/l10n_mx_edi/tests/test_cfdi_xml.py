# -*- coding: utf-8 -*-
from .common import TestMxEdiCommon
from odoo.tests import tagged
from odoo.exceptions import ValidationError

from freezegun import freeze_time


@tagged('post_install', '-at_install')
class TestEdiResults(TestMxEdiCommon):

    # -------------------------------------------------------------------------
    # INVOICES
    # -------------------------------------------------------------------------

    def test_invoice_cfdi_no_external_trade(self):
        with freeze_time(self.frozen_today):
            self.invoice.action_post()

            generated_files = self._process_documents_web_services(self.invoice, {'cfdi_3_3'})
            self.assertTrue(generated_files)
            cfdi = generated_files[0]

            current_etree = self.get_xml_tree_from_string(cfdi)
            expected_etree = self.get_xml_tree_from_string(self.expected_invoice_cfdi_values)
            self.assertXmlTreeEqual(current_etree, expected_etree)

    def test_invoice_cfdi_group_of_taxes(self):
        with freeze_time(self.frozen_today):
            self.invoice.write({
                'invoice_line_ids': [(1, self.invoice.invoice_line_ids.id, {'tax_ids': [(6, 0, self.tax_group.ids)]})],
            })
            self.invoice.action_post()

            generated_files = self._process_documents_web_services(self.invoice, {'cfdi_3_3'})
            self.assertTrue(generated_files)
            cfdi = generated_files[0]

            current_etree = self.get_xml_tree_from_string(cfdi)
            expected_etree = self.get_xml_tree_from_string(self.expected_invoice_cfdi_values)
            self.assertXmlTreeEqual(current_etree, expected_etree)

    def test_invoice_cfdi_addenda(self):
        with freeze_time(self.frozen_today):

            # Setup an addenda on the partner.
            self.invoice.partner_id.l10n_mx_edi_addenda = self.env['ir.ui.view'].create({
                'name': 'test_invoice_cfdi_addenda',
                'type': 'qweb',
                'arch': """
                    <t t-name="l10n_mx_edi.test_invoice_cfdi_addenda">
                        <test info="this is an addenda"/>
                    </t>
                """
            })

            self.invoice.action_post()

            generated_files = self._process_documents_web_services(self.invoice, {'cfdi_3_3'})
            self.assertTrue(generated_files)
            cfdi = generated_files[0]

            current_etree = self.get_xml_tree_from_string(cfdi)
            expected_etree = self.with_applied_xpath(
                self.get_xml_tree_from_string(self.expected_invoice_cfdi_values),
                '''
                    <xpath expr="//Comprobante" position="inside">
                        <Addenda>
                            <test info="this is an addenda"/>
                        </Addenda>
                    </xpath>
                ''',
            )
            self.assertXmlTreeEqual(current_etree, expected_etree)

    # -------------------------------------------------------------------------
    # PAYMENTS
    # -------------------------------------------------------------------------

    def test_payment_cfdi(self):
        with freeze_time(self.frozen_today):
            self.payment.payment_id.action_l10n_mx_edi_force_generate_cfdi()
            self.invoice.action_post()
            self.payment.action_post()

            (self.invoice.line_ids + self.payment.line_ids)\
                .filtered(lambda line: line.account_internal_type == 'receivable')\
                .reconcile()

            # Fake the fact the invoice is signed.
            self._process_documents_web_services(self.invoice)
            self.invoice.l10n_mx_edi_cfdi_uuid = '123456789'

            generated_files = self._process_documents_web_services(self.payment.move_id, {'cfdi_3_3'})
            self.assertTrue(generated_files)
            cfdi = generated_files[0]

            current_etree = self.get_xml_tree_from_string(cfdi)
            expected_etree = self.get_xml_tree_from_string(self.expected_payment_cfdi_values)
            self.assertXmlTreeEqual(current_etree, expected_etree)

    # -------------------------------------------------------------------------
    # STATEMENT LINES
    # -------------------------------------------------------------------------

    def test_statement_line_cfdi(self):
        with freeze_time(self.frozen_today):
            self.statement_line.action_l10n_mx_edi_force_generate_cfdi()
            self.invoice.action_post()
            self.statement.button_post()

            receivable_line = self.invoice.line_ids.filtered(lambda line: line.account_internal_type == 'receivable')
            self.statement_line.reconcile([{'id': receivable_line.id}])

            # Fake the fact the invoice is signed.
            self._process_documents_web_services(self.invoice)
            self.invoice.l10n_mx_edi_cfdi_uuid = '123456789'

            generated_files = self._process_documents_web_services(self.statement_line.move_id, {'cfdi_3_3'})
            self.assertTrue(generated_files)
            cfdi = generated_files[0]

            current_etree = self.get_xml_tree_from_string(cfdi)
            expected_etree = self.with_applied_xpath(
                self.get_xml_tree_from_string(self.expected_payment_cfdi_values),
                '''
                    <xpath expr="//Comprobante" position="attributes">
                        <attribute name="Folio">2</attribute>
                    </xpath>
                ''',
            )
            self.assertXmlTreeEqual(current_etree, expected_etree)
