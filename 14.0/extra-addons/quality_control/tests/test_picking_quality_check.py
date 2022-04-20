# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from .test_common import TestQualityCommon

class TestQualityCheck(TestQualityCommon):

    def test_00_picking_quality_check(self):

        """Test quality check on incoming shipment."""

        # Create Quality Point for incoming shipment.
        self.qality_point_test = self.env['quality.point'].create({
            'product_ids': [(4, self.product.id)],
            'picking_type_ids': [(4, self.picking_type_id)],
        })

        # Check that quality point created.
        self.assertTrue(self.qality_point_test, "First Quality Point not created for Laptop Customized.")

        # Create incoming shipment.
        self.picking_in = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_id,
            'partner_id': self.partner_id,
            'location_id': self.location_id,
            'location_dest_id': self.location_dest_id,
        })
        self.env['stock.move'].create({
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom_qty': 2,
            'product_uom': self.product.uom_id.id,
            'picking_id': self.picking_in.id,
            'location_id': self.location_id,
            'location_dest_id': self.location_dest_id})

        # Check that incoming shipment is created.
        self.assertTrue(self.picking_in, "Incoming shipment not created.")

        # Confirm incoming shipment.
        self.picking_in.action_confirm()

        # Check Quality Check for incoming shipment is created and check it's state is 'none'.
        self.assertEqual(len(self.picking_in.check_ids), 1)
        self.assertEqual(self.picking_in.check_ids.quality_state, 'none')

        # 'Pass' Quality Checks of incoming shipment.
        self.picking_in.check_ids.do_pass()

        # Validate incoming shipment.
        self.picking_in.button_validate()

        # Now check state of quality check.
        self.assertEqual(self.picking_in.check_ids.quality_state, 'pass')

    def test_01_picking_quality_check_type_text(self):

        """ Test a Quality Check on a picking with 'Instruction'
        as test type.
        """
        # Create Quality Point for incoming shipment with 'Instructions' as test type
        self.qality_point_test = self.env['quality.point'].create({
            'product_ids': [(4, self.product.id)],
            'picking_type_ids': [(4, self.picking_type_id)],
            'test_type_id': self.env.ref('quality.test_type_instructions').id
        })

        # Check that quality point created.
        self.assertTrue(self.qality_point_test, "Quality Point not created")

        # Create incoming shipment.
        self.picking_in = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_id,
            'partner_id': self.partner_id,
            'location_id': self.location_id,
            'location_dest_id': self.location_dest_id,
        })
        self.env['stock.move'].create({
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom_qty': 2,
            'product_uom': self.product.uom_id.id,
            'picking_id': self.picking_in.id,
            'location_id': self.location_id,
            'location_dest_id': self.location_dest_id})

        # Check that incoming shipment is created.
        self.assertTrue(self.picking_in, "Incoming shipment not created.")

        # Confirm incoming shipment.
        self.picking_in.action_confirm()

        # Check Quality Check for incoming shipment is created and check it's state is 'none'.
        self.assertEqual(len(self.picking_in.check_ids), 1)
        self.assertEqual(self.picking_in.check_ids.quality_state, 'none')

        # Check that the Quality Check on the picking has 'instruction' as test_type
        self.assertEqual(self.picking_in.check_ids[0].test_type, 'instructions')

    def test_02_picking_quality_check_type_picture(self):

        """ Test a Quality Check on a picking with 'Take Picture'
        as test type.
        """
        # Create Quality Point for incoming shipment with 'Take Picture' as test type
        self.qality_point_test = self.env['quality.point'].create({
            'product_ids': [(4, self.product.id)],
            'picking_type_ids': [(4, self.picking_type_id)],
            'test_type_id': self.env.ref('quality.test_type_picture').id
        })
        # Check that quality point created.
        self.assertTrue(self.qality_point_test, "Quality Point not created")
        # Create incoming shipment.
        self.picking_in = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_id,
            'partner_id': self.partner_id,
            'location_id': self.location_id,
            'location_dest_id': self.location_dest_id,
        })
        self.env['stock.move'].create({
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom_qty': 2,
            'product_uom': self.product.uom_id.id,
            'picking_id': self.picking_in.id,
            'location_id': self.location_id,
            'location_dest_id': self.location_dest_id})
        # Check that incoming shipment is created.
        self.assertTrue(self.picking_in, "Incoming shipment not created.")
        # Confirm incoming shipment.
        self.picking_in.action_confirm()
        # Check Quality Check for incoming shipment is created and check it's state is 'none'.
        self.assertEqual(len(self.picking_in.check_ids), 1)
        self.assertEqual(self.picking_in.check_ids.quality_state, 'none')

        # Check that the Quality Check on the picking has 'picture' as test_type
        self.assertEqual(self.picking_in.check_ids[0].test_type, 'picture')
