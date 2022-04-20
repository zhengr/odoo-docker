# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api


class PlanningTemplate(models.Model):
    _inherit = 'planning.slot.template'

    project_id = fields.Many2one('project.project', compute='_compute_project_id', store=True, readonly=False, string="Project", domain="[('company_id', '=', company_id), ('allow_forecast', '=', True)]")
    task_id = fields.Many2one('project.task', string="Task", domain="[('company_id', '=', company_id), ('project_id', '=?', project_id)]")

    def name_get(self):
        name_template = super(PlanningTemplate, self).name_get()
        name_dict = dict([(x[0], x[1]) for x in name_template])
        result = []
        for shift_template in self:
            if shift_template.project_id and shift_template.task_id:
                name = '%s [%s - %s]' % (name_dict[shift_template.id], shift_template.project_id.display_name[:30], shift_template.task_id.display_name[:30])
            elif shift_template.project_id:
                name = '%s [%s]' % (name_dict[shift_template.id], shift_template.project_id.display_name[:30])
            else:
                name = name_dict[shift_template.id]
            result.append([shift_template.id, name])
        return result

    @api.depends('task_id')
    def _compute_project_id(self):
        for slot in self:
            if slot.task_id:
                slot.project_id = slot.task_id.project_id
