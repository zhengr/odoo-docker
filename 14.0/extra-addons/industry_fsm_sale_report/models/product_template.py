# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    worksheet_template_id = fields.Many2one(
        'project.worksheet.template', string="Worksheet Template",
        compute='_compute_worksheet_template_id', store=True, readonly=False)

    @api.depends('service_tracking', 'project_id')
    def _compute_worksheet_template_id(self):
        for template in self:
            if template.service_tracking not in ['task_global_project', 'task_new_project']:
                template.worksheet_template_id = False

            if template.project_id.is_fsm:
                template.worksheet_template_id = template.project_id.worksheet_template_id
            else:
                template.worksheet_template_id = False
