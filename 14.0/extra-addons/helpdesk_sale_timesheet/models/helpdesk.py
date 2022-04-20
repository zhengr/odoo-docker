# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ast import literal_eval
from odoo import api, fields, models, _

from odoo.addons.sale_timesheet_enterprise.models.sale import DEFAULT_INVOICED_TIMESHEET


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    def _create_project(self, name, allow_billable, other):
        new_values = dict(other, allow_billable=allow_billable)
        return super(HelpdeskTeam, self)._create_project(name, allow_billable, new_values)


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    use_helpdesk_sale_timesheet = fields.Boolean('Reinvoicing Timesheet activated on Team', related='team_id.use_helpdesk_sale_timesheet', readonly=True)
    display_create_so_button_primary = fields.Boolean(compute="_compute_sale_order_button_visibility", compute_sudo=True)
    display_create_so_button_secondary = fields.Boolean(compute="_compute_sale_order_button_visibility", compute_sudo=True)
    sale_order_id = fields.Many2one('sale.order', compute="_compute_helpdesk_sale_order", compute_sudo=True, store=True, readonly=False)

    @api.depends('project_id', 'use_helpdesk_sale_timesheet', 'partner_id.commercial_partner_id')
    def _compute_related_task_ids(self):
        reinvoiced = self.filtered(lambda t: t.project_id and t.use_helpdesk_sale_timesheet and t.partner_id)
        for t in reinvoiced:
            t._related_task_ids = self.env['project.task'].search([
                ('project_id', '=', t.project_id.id),
                '|', ('partner_id', '=', False),
                     ('partner_id', 'child_of', t.partner_id.commercial_partner_id.id)
            ])._origin
        super(HelpdeskTicket, self - reinvoiced)._compute_related_task_ids()

    @api.depends('use_helpdesk_sale_timesheet', 'project_id.allow_billable', 'project_id.sale_order_id', 'task_id.sale_line_id', 'total_hours_spent')
    def _compute_sale_order_button_visibility(self):
        for ticket in self:
            primary, secondary = False, False
            if ticket.use_helpdesk_sale_timesheet:
                if ticket.project_id and not ticket.project_id.allow_billable and \
                        not ticket.project_id.sale_order_id:
                    if ticket.total_hours_spent > 0:
                        primary = True
                    else:
                        secondary = True
                elif ticket.project_id and ticket.project_id.allow_billable and \
                        ticket.task_id and not ticket.task_id.sale_line_id:
                    if ticket.total_hours_spent > 0:
                        primary = True
                    else:
                        secondary = True
            ticket.display_create_so_button_primary = primary
            ticket.display_create_so_button_secondary = secondary

    def create_sale_order(self):
        self.ensure_one()
        if self.project_id.allow_billable:
            # open project.task create sale order wizard
            if self.partner_id:
                customer = self.partner_id.id
            else:
                customer = self.task_id.partner_id.id

            return {
                "name": _("Create Sales Order"),
                "type": 'ir.actions.act_window',
                "res_model": 'project.task.create.sale.order',
                "views": [[False, "form"]],
                "target": 'new',
                "context": {
                    'active_id': self.task_id.id,
                    'active_model': 'project.task',
                    'form_view_initial_mode': 'edit',
                    'default_partner_id': customer,
                    'default_product_id': self.env.ref('sale_timesheet.time_product').id,
                },
            }
        # open project.project create sale order wizard
        if self.partner_id:
            customer = self.partner_id.id
        else:
            customer = self.project_id.partner_id.id

        return {
            "name": _("Create Sales Order"),
            "type": 'ir.actions.act_window',
            "res_model": 'project.create.sale.order',
            "views": [[False, "form"]],
            "target": 'new',
            "context": {
                'active_id': self.project_id.id,
                'active_model': 'project.project',
                'default_partner_id': customer,
                'default_product_id': self.env.ref('sale_timesheet.time_product').id,
            },
        }

    @api.depends('project_id.sale_order_id', 'task_id.sale_order_id')
    def _compute_helpdesk_sale_order(self):
        for ticket in self:
            if ticket.project_id.sale_order_id:
                ticket.sale_order_id = ticket.project_id.sale_order_id
            elif ticket.task_id.sale_order_id:
                ticket.sale_order_id = ticket.task_id.sale_order_id
            if ticket.sale_order_id and not ticket.partner_id:
                ticket.partner_id = ticket.sale_order_id.partner_id


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def _timesheet_preprocess(self, values):
        values = super(AccountAnalyticLine, self)._timesheet_preprocess(values)
        # TODO JEM: clean this. Need to set the SOL when changing the task in order to always have the SOL in project map, or task'SOL or SOL of the project (python constraint)
        if 'task_id' in values and not values.get('so_line'):
            task = self.env['project.task'].sudo().browse(values['task_id'])
            if task.bill_type == 'customer_project' and task.pricing_type == 'fixed_rate':
                values['so_line'] = task.sale_line_id.id
        return values

    def _get_portal_helpdesk_timesheet(self):
        param_invoiced_timesheet = self.env['ir.config_parameter'].sudo().get_param('sale.invoiced_timesheet', DEFAULT_INVOICED_TIMESHEET)
        if param_invoiced_timesheet == 'approved':
            return self.filtered(lambda line: line.validated)
        return self
