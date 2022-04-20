# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import Form

from .test_common import TestQualityMrpCommon

class TestQualityCheck(TestQualityMrpCommon):

    def test_00_production_quality_check(self):

        """Test quality check on production order."""

        # Create Quality Point for product Laptop Customized with Manufacturing Operation Type.
        self.qality_point_test1 = self.env['quality.point'].create({
            'product_ids': [(4, self.product_id)],
            'picking_type_ids': [(4, self.picking_type_id)],
        })

        # Check that quality point created.
        assert self.qality_point_test1, "First Quality Point not created for Laptop Customized."

        # Create Production Order of Laptop Customized to produce 5.0 Unit.
        production_form = Form(self.env['mrp.production'])
        production_form.product_id = self.env['product.product'].browse(self.product_id)
        production_form.product_qty = 5.0
        self.mrp_production_qc_test1 = production_form.save()

        # Check that Production Order of Laptop Customized to produce 5.0 Unit is created.
        assert self.mrp_production_qc_test1, "Production Order not created."

        # Perform check availability and produce product.
        self.mrp_production_qc_test1.action_confirm()
        self.mrp_production_qc_test1.action_assign()

        mo_form = Form(self.mrp_production_qc_test1)
        mo_form.qty_producing = self.mrp_production_qc_test1.product_qty
        mo_form.lot_producing_id = self.lot_product_27_0
        details_operation_form = Form(self.mrp_production_qc_test1.move_raw_ids[0], view=self.env.ref('stock.view_stock_move_operations'))
        with details_operation_form.move_line_ids.new() as ml:
            ml.qty_done = self.mrp_production_qc_test1.product_qty
        details_operation_form.save()

        self.mrp_production_qc_test1 = mo_form.save()
        # Check Quality Check for Production is created and check it's state is 'none'.
        self.assertEqual(len(self.mrp_production_qc_test1.check_ids), 1)
        self.assertEqual(self.mrp_production_qc_test1.check_ids.quality_state, 'none')

        # 'Pass' Quality Checks of production order.
        self.mrp_production_qc_test1.check_ids.do_pass()

        # Set MO Done.
        self.mrp_production_qc_test1.button_mark_done()

        # Now check state of quality check.
        self.assertEqual(self.mrp_production_qc_test1.check_ids.quality_state, 'pass')
