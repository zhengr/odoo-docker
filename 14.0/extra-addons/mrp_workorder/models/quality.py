# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.osv.expression import OR


class TestType(models.Model):
    _inherit = "quality.point.test_type"

    allow_registration = fields.Boolean(search='_get_domain_from_allow_registration',
            store=False, default=False)

    def _get_domain_from_allow_registration(self, operator, value):
        if value:
            return []
        else:
            return [('technical_name', 'not in', ['register_byproducts', 'register_consumed_materials', 'print_label'])]


class MrpRouting(models.Model):
    _inherit = "mrp.routing.workcenter"

    quality_point_ids = fields.One2many('quality.point', 'operation_id')
    quality_point_count = fields.Integer('Steps', compute='_compute_quality_point_count')

    @api.depends('quality_point_ids')
    def _compute_quality_point_count(self):
        read_group_res = self.env['quality.point'].sudo().read_group(
            [('id', 'in', self.quality_point_ids.ids)],
            ['operation_id'], 'operation_id'
        )
        data = dict((res['operation_id'][0], res['operation_id_count']) for res in read_group_res)
        for operation in self:
            operation.quality_point_count = data.get(operation.id, 0)

    def action_mrp_workorder_show_steps(self):
        self.ensure_one()
        picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'mrp_operation')], limit=1).id
        action = self.env["ir.actions.actions"]._for_xml_id("mrp_workorder.action_mrp_workorder_show_steps")
        # Can pass the default product in the context when coming from the BOM view, but as BOM use
        # `product.template` and quality points use `product.product`, we need to convert the id.
        if self.env.context.get('default_product_tmpl_ids') and not self.env.context.get('default_product_ids'):
            product_templates = self.env['product.template'].search_read(
                [('id', 'in', self.env.context.get('default_product_tmpl_ids'))],
                ['product_variant_ids']
            )
            product_ids = [pid for template in product_templates for pid in template['product_variant_ids']]
            self.env.context = dict(self.env.context, default_product_ids=product_ids)
        ctx = dict(self._context, default_picking_type_id=picking_type_id, default_company_id=self.company_id.id)
        action.update({'context': ctx, 'domain': [('operation_id', '=', self.id)]})
        return action


class QualityPoint(models.Model):
    _inherit = "quality.point"

    is_workorder_step = fields.Boolean(compute='_compute_is_workorder_step')
    operation_id = fields.Many2one(
        'mrp.routing.workcenter', 'Step', check_company=True)
    bom_id = fields.Many2one(related='operation_id.bom_id', readonly=False)
    component_ids = fields.One2many('product.product', compute='_compute_component_ids')
    test_type_id = fields.Many2one(
        'quality.point.test_type',
        domain="[('allow_registration', '=', operation_id and is_workorder_step)]")
    test_report_type = fields.Selection([('pdf', 'PDF'), ('zpl', 'ZPL')], string="Report Type", default="pdf", required=True)
    worksheet = fields.Selection([
        ('noupdate', 'Do not update page'),
        ('scroll', 'Scroll to specific page')], string="Worksheet",
        default="noupdate")
    worksheet_page = fields.Integer('Worksheet Page')
    # Used with type register_consumed_materials the product raw to encode.
    component_id = fields.Many2one('product.product', 'Product To Register', check_company=True)

    @api.depends('bom_id.product_id', 'bom_id.product_tmpl_id.product_variant_ids', 'is_workorder_step')
    def _compute_available_product_ids(self):
        super()._compute_available_product_ids()
        points_for_workorder_step = self.filtered(lambda p: p.is_workorder_step)
        for point in points_for_workorder_step:
            point.available_product_ids = point.bom_id.product_id or point.bom_id.product_tmpl_id.product_variant_ids

    @api.depends('product_ids', 'test_type_id')
    def _compute_component_ids(self):
        self.component_ids = False
        points = self.filtered(
            lambda p: p.is_workorder_step and p.test_type in [
                'register_consumed_materials',
                'register_byproducts'
            ])
        bom_domain = OR([self.env['mrp.bom']._bom_find_domain(product=product._origin, bom_type='normal') for product in points.product_ids])
        bom_ids = self.env['mrp.bom'].search(bom_domain)
        product_by_points = defaultdict(lambda: self.env['quality.point'])
        for point in points:
            for product in point.product_ids:
                product_by_points[product._origin] |= point

        for bom in bom_ids:
            bom_products = bom.product_id or bom.product_tmpl_id.product_variant_ids
            byproducts = bom.byproduct_ids.product_id
            for product in bom_products:
                if product not in product_by_points:
                    continue
                dummy, lines_done = bom.explode(product, 1.0)
                components = self.env['product.product'].browse([line[0].product_id.id for line in lines_done])
            for point in product_by_points[product]:
                if point.test_type == 'register_consumed_materials':
                    point.component_ids |= components
                else:
                    point.component_ids |= byproducts

    @api.depends('operation_id', 'picking_type_ids')
    def _compute_is_workorder_step(self):
        for quality_point in self:
            quality_point.is_workorder_step = quality_point.operation_id or quality_point.picking_type_ids and\
                all(pt.code == 'mrp_operation' for pt in quality_point.picking_type_ids)


class QualityAlert(models.Model):
    _inherit = "quality.alert"

    workorder_id = fields.Many2one('mrp.workorder', 'Operation', check_company=True)
    workcenter_id = fields.Many2one('mrp.workcenter', 'Work Center', check_company=True)
    production_id = fields.Many2one('mrp.production', "Production Order", check_company=True)


class QualityCheck(models.Model):
    _inherit = "quality.check"

    workorder_id = fields.Many2one(
        'mrp.workorder', 'Operation', check_company=True)
    workcenter_id = fields.Many2one('mrp.workcenter', related='workorder_id.workcenter_id', store=True, readonly=True)  # TDE: necessary ?
    production_id = fields.Many2one(
        'mrp.production', 'Production Order', check_company=True)

    # doubly linked chain for tablet view navigation
    next_check_id = fields.Many2one('quality.check')
    previous_check_id = fields.Many2one('quality.check')

    # For components registration
    move_id = fields.Many2one(
        'stock.move', 'Stock Move', check_company=True)
    move_line_id = fields.Many2one(
        'stock.move.line', 'Stock Move Line', check_company=True)
    component_id = fields.Many2one(
        'product.product', 'Component', check_company=True)
    component_uom_id = fields.Many2one('uom.uom', related='move_id.product_uom', readonly=True)

    qty_done = fields.Float('Done', default=1.0, digits='Product Unit of Measure')
    finished_lot_id = fields.Many2one('stock.production.lot', 'Finished Lot/Serial', related='production_id.lot_producing_id')
    additional = fields.Boolean('Register additionnal product', compute='_compute_additional')

    # Computed fields
    title = fields.Char('Title', compute='_compute_title')
    result = fields.Char('Result', compute='_compute_result')
    quality_state_for_summary = fields.Char('Status Summary', compute='_compute_result')

    # Used to group the steps belonging to the same production
    # We use a float because it is actually filled in by the produced quantity at the step creation.
    finished_product_sequence = fields.Float('Finished Product Sequence Number')

    @api.model_create_multi
    def create(self, values):
        points = self.env['quality.point'].search([
            ('id', 'in', [value.get('point_id') for value in values]),
            ('component_id', '!=', False)
        ])
        for value in values:
            if not value.get('component_id') and value.get('point_id'):
                point = points.filtered(lambda p: p.id == value.get('point_id'))
                if point:
                    value['component_id'] = point.component_id.id
        return super(QualityCheck, self).create(values)

    def _compute_title(self):
        super()._compute_title()
        for check in self:
            if not check.point_id or check.component_id:
                check.title = '{} "{}"'.format(check.test_type_id.display_name, check.component_id.name)

    @api.depends('point_id', 'quality_state', 'component_id', 'component_uom_id', 'lot_id', 'qty_done')
    def _compute_result(self):
        for check in self:
            state = check.quality_state
            check.quality_state_for_summary = _('Done') if state != 'none' else _('To Do')
            if check.quality_state == 'none':
                check.result = ''
            else:
                check.result = check._get_check_result()

    @api.depends('move_id')
    def _compute_additional(self):
        """ The stock_move is linked to additional workorder line only at
        record_production. So line without move during production are additionnal
        ones. """
        for check in self:
            check.additional = not check.move_id

    def _get_check_result(self):
        if self.test_type in ('register_consumed_materials', 'register_byproducts') and self.lot_id:
            return '{} - {}, {} {}'.format(self.component_id.name, self.lot_id.name, self.qty_done, self.component_uom_id.name)
        elif self.test_type in ('register_consumed_materials', 'register_byproducts'):
            return '{}, {} {}'.format(self.component_id.name, self.qty_done, self.component_uom_id.name)
        else:
            return ''

    def _insert_in_chain(self, position, relative):
        """Insert the quality check `self` in a chain of quality checks.

        The chain of quality checks is implicitly given by the `relative` argument,
        i.e. by following its `previous_check_id` and `next_check_id` fields.

        :param position: Where we need to insert `self` according to `relative`
        :type position: string
        :param relative: Where we need to insert `self` in the chain
        :type relative: A `quality.check` record.
        """
        self.ensure_one()
        assert position in ['before', 'after']
        if position == 'before':
            new_previous = relative.previous_check_id
            self.next_check_id = relative
            self.previous_check_id = new_previous
            new_previous.next_check_id = self
            relative.previous_check_id = self
        else:
            new_next = relative.next_check_id
            self.next_check_id = new_next
            self.previous_check_id = relative
            new_next.previous_check_id = self
            relative.next_check_id = self
