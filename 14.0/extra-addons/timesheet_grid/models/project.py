# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class Project(models.Model):
    _inherit = "project.project"

    allow_timesheet_timer = fields.Boolean(
        'Timesheet Timer',
        compute='_compute_allow_timesheet_timer',
        readonly=False,
        store=True,
        help="Use a timer to record timesheets on tasks")

    _sql_constraints = [
        ('timer_only_when_timesheet', "CHECK((allow_timesheets = 'f' AND allow_timesheet_timer = 'f') OR (allow_timesheets = 't'))", 'The timesheet timer can only be activated on project allowing timesheets.'),
    ]

    @api.depends('allow_timesheets')
    def _compute_allow_timesheet_timer(self):
        for project in self:
            project.allow_timesheet_timer = project.allow_timesheets

    def write(self, values):
        result = super(Project, self).write(values)
        if 'allow_timesheet_timer' in values and not values.get('allow_timesheet_timer'):
            self.env['timer.timer'].search([
                ('res_model', '=', "project.task"),
                ('res_id', 'in', self.with_context(active_test=False).task_ids.ids)
            ]).unlink()
        return result
