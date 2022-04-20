# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval


class LoyaltyProgram(models.Model):
    _name = 'loyalty.program'
    _description = 'Loyalty Program'

    name = fields.Char(string='Loyalty Program Name', index=True, required=True, help="An internal identification for the loyalty program configuration")
    points = fields.Float(string='Point per $ spent', help="How many loyalty points are given to the customer by sold currency")
    rule_ids = fields.One2many('loyalty.rule', 'loyalty_program_id', string='Rules')
    reward_ids = fields.One2many('loyalty.reward', 'loyalty_program_id', string='Rewards')
    active = fields.Boolean(default=True)


class LoyaltyRule(models.Model):
    _name = 'loyalty.rule'
    _description = 'Loyalty Rule'

    name = fields.Char(index=True, required=True, help="An internal identification for this loyalty program rule")
    loyalty_program_id = fields.Many2one('loyalty.program', string='Loyalty Program', help='The Loyalty Program this exception belongs to')
    points_quantity = fields.Float(string="Points per Unit")
    points_currency = fields.Float(string="Points per $ spent")
    rule_domain = fields.Char()
    valid_product_ids = fields.One2many('product.product', compute='_compute_valid_product_ids')

    @api.depends('rule_domain')
    def _compute_valid_product_ids(self):
        for rule in self:
            if rule.rule_domain:
                domain = safe_eval(rule.rule_domain)
                domain = expression.AND([domain, [('available_in_pos', '=', True)]])
                rule.valid_product_ids = self.env['product.product'].search(domain)
            else:
                rule.valid_product_ids = self.env['product.product'].search([('available_in_pos', '=', True)])


class LoyaltyReward(models.Model):
    _name = 'loyalty.reward'
    _description = 'Loyalty Reward'

    name = fields.Char(index=True, required=True, help='An internal identification for this loyalty reward')
    loyalty_program_id = fields.Many2one('loyalty.program', string='Loyalty Program', help='The Loyalty Program this reward belongs to')
    minimum_points = fields.Float(help='The minimum amount of points the customer must have to qualify for this reward')
    reward_type = fields.Selection([('gift', 'Free Product'), ('discount', 'Discount')], required=True, help='The type of the reward', default="gift")
    gift_product_id = fields.Many2one('product.product', string='Gift Product', help='The product given as a reward')
    point_cost = fields.Float(string='Reward Cost', help="If the reward is a gift, that's the cost of the gift in points. If the reward type is a discount that's the cost in point per currency (e.g. 1 point per $)")
    discount_product_id = fields.Many2one('product.product', string='Discount Product', help='The product used to apply discounts')
    discount_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount')], default="percentage",
        help="Percentage - Entered percentage discount will be provided\n" +
             "Amount - Entered fixed amount discount will be provided")
    discount_percentage = fields.Float(string="Discount", default=10,
                                       help='The discount in percentage, between 1 to 100')
    discount_apply_on = fields.Selection([
        ('on_order', 'On Order'),
        ('cheapest_product', 'On Cheapest Product'),
        ('specific_products', 'On Specific Products')], default="on_order",
        help="On Order - Discount on whole order\n" +
             "Cheapest product - Discount on cheapest product of the order\n" +
             "Specific products - Discount on selected specific products")
    discount_specific_product_ids = fields.Many2many('product.product', string="Products",
                                                     help="Products that will be discounted if the discount is applied on specific products")
    discount_max_amount = fields.Float(default=0,
                                       help="Maximum amount of discount that can be provided")
    discount_fixed_amount = fields.Float(string="Fixed Amount", help='The discount in fixed amount')
    minimum_amount = fields.Float(string="Minimum Order Amount")

    @api.constrains('reward_type', 'gift_product_id')
    def _check_gift_product(self):
        if self.filtered(lambda reward: reward.reward_type == 'gift' and not reward.gift_product_id):
            raise ValidationError(_('The gift product field is mandatory for gift rewards'))

    @api.constrains('reward_type', 'discount_product_id')
    def _check_discount_product(self):
        if self.filtered(lambda reward: reward.reward_type == 'discount' and not reward.discount_product_id):
            raise ValidationError(_('The discount product field is mandatory for discount rewards'))
