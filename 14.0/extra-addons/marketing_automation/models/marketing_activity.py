# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
import threading

from ast import literal_eval
from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.fields import Datetime
from odoo.exceptions import ValidationError, AccessError
from odoo.osv import expression

_logger = logging.getLogger(__name__)



class MarketingActivity(models.Model):
    _name = 'marketing.activity'
    _description = 'Marketing Activity'
    _inherits = {'utm.source': 'utm_source_id'}
    _order = 'interval_standardized'

    # definition and UTM
    activity_type = fields.Selection([
        ('email', 'Email'),
        ('action', 'Server Action')
        ], string='Activity Type', required=True, default='email')
    mass_mailing_id = fields.Many2one(
        'mailing.mailing', string='Marketing Template', compute='_compute_mass_mailing_id',
        readonly=False, store=True)
    mass_mailing_id_mailing_type = fields.Selection([
        ('mail', 'Email')], string='Mailing Type', compute='_compute_mass_mailing_id_mailing_type',
        readonly=True, store=True, help='Technical field doing the mapping of activity type and mailing type.')
    server_action_id = fields.Many2one(
        'ir.actions.server', string='Server Action', compute='_compute_server_action_id',
        readonly=False, store=True)
    utm_source_id = fields.Many2one('utm.source', 'Source', ondelete='cascade', required=True)
    campaign_id = fields.Many2one(
        'marketing.campaign', string='Campaign',
        index=True, ondelete='cascade', required=True)
    utm_campaign_id = fields.Many2one(
        'utm.campaign', string='UTM Campaign',
        readonly=True, related='campaign_id.utm_campaign_id')  # propagate to mailings
    # interval
    interval_number = fields.Integer(string='Send after', default=1)
    interval_type = fields.Selection([
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months')], string='Delay Type',
        default='hours', required=True)
    interval_standardized = fields.Integer('Send after (in hours)', compute='_compute_interval_standardized', store=True, readonly=True)
    # validity
    validity_duration = fields.Boolean('Validity Duration',
        help='Check this to make sure your actions are not executed after a specific amount of time after the scheduled date. (e.g. : Time-limited offer, Upcoming event, …)')
    validity_duration_number = fields.Integer(string='Valid during', default=0)
    validity_duration_type = fields.Selection([
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months')],
        default='hours', required=True)
    # target
    domain = fields.Char(
        string='Applied Filter', default='[]',
        help='Activity will only be performed if record satisfies this domain, obtained from the combination of the activity filter and its inherited filter',
        compute='_compute_inherited_domain', store=True, readonly=True)
    activity_domain = fields.Char(
        string='Activity Filter', default='[]',
        help='Domain that applies to this activity and its child activities')
    model_id = fields.Many2one('ir.model', related='campaign_id.model_id', string='Model', readonly=True)
    model_name = fields.Char(related='model_id.model', string='Model Name', readonly=True)
    # Related to parent activity
    parent_id = fields.Many2one(
        'marketing.activity', string='Activity', compute='_compute_parent_id',
        index=True, readonly=False, store=True, ondelete='cascade')
    allowed_parent_ids = fields.Many2many('marketing.activity', string='Allowed parents', help='All activities which can be the parent of this one', compute='_compute_allowed_parent_ids')
    child_ids = fields.One2many('marketing.activity', 'parent_id', string='Child Activities')
    trigger_type = fields.Selection([
        ('begin', 'beginning of campaign'),
        ('activity', 'another activity'),
        ('mail_open', 'Mail: opened'),
        ('mail_not_open', 'Mail: not opened'),
        ('mail_reply', 'Mail: replied'),
        ('mail_not_reply', 'Mail: not replied'),
        ('mail_click', 'Mail: clicked'),
        ('mail_not_click', 'Mail: not clicked'),
        ('mail_bounce', 'Mail: bounced')], default='begin', required=True)
    trigger_category = fields.Selection([('email', 'Mail')], compute='_compute_trigger_category')
    # cron / updates
    require_sync = fields.Boolean('Require trace sync', copy=False)
    # For trace
    trace_ids = fields.One2many('marketing.trace', 'activity_id', string='Traces', copy=False)
    processed = fields.Integer(compute='_compute_statistics')
    rejected = fields.Integer(compute='_compute_statistics')
    total_sent = fields.Integer(compute='_compute_statistics')
    total_click = fields.Integer(compute='_compute_statistics')
    total_open = fields.Integer(compute='_compute_statistics')
    total_reply = fields.Integer(compute='_compute_statistics')
    total_bounce = fields.Integer(compute='_compute_statistics')
    statistics_graph_data = fields.Char(compute='_compute_statistics_graph_data')

    @api.constrains('trigger_type', 'parent_id')
    def _check_consistency_in_activities(self):
        """Check the consistency in the activity chaining."""
        for activity in self:
            if (activity.parent_id or activity.allowed_parent_ids) and activity.parent_id not in activity.allowed_parent_ids:
                trigger_string = dict(activity._fields['trigger_type']._description_selection(self.env))[activity.trigger_type]
                raise ValidationError(
                    _('You are trying to set the activity "%s" as "%s" while its child "%s" has the trigger type "%s"\nPlease modify one of those activities before saving.')
                    % (activity.parent_id.name, activity.parent_id.activity_type, activity.name, trigger_string))

    @api.depends('activity_type')
    def _compute_mass_mailing_id_mailing_type(self):
        for activity in self:
            if activity.activity_type == 'email':
                activity.mass_mailing_id_mailing_type = 'mail'
            elif activity.activity_type == 'action':
                activity.mass_mailing_id_mailing_type = False

    @api.depends('mass_mailing_id_mailing_type')
    def _compute_mass_mailing_id(self):
        for activity in self:
            if activity.mass_mailing_id_mailing_type != activity.mass_mailing_id.mailing_type:
                activity.mass_mailing_id = False

    @api.depends('activity_type')
    def _compute_server_action_id(self):
        for activity in self:
            if activity.activity_type != 'action':
                activity.server_action_id = False

    @api.depends('activity_domain', 'campaign_id.domain', 'parent_id.domain')
    def _compute_inherited_domain(self):
        for activity in self:
            domain = expression.AND([literal_eval(activity.activity_domain),
                                     literal_eval(activity.campaign_id.domain)])
            ancestor = activity.parent_id
            while ancestor:
                domain = expression.AND([domain, literal_eval(ancestor.activity_domain)])
                ancestor = ancestor.parent_id
            activity.domain = domain

    @api.depends('interval_type', 'interval_number')
    def _compute_interval_standardized(self):
        factors = {'hours': 1,
                   'days': 24,
                   'weeks': 168,
                   'months': 720}
        for activity in self:
            activity.interval_standardized = activity.interval_number * factors[activity.interval_type]

    @api.depends('trigger_type')
    def _compute_parent_id(self):
        for activity in self:
            if not activity.parent_id or (activity.parent_id and activity.trigger_type == 'begin'):
                activity.parent_id = False

    @api.depends('trigger_type', 'campaign_id.marketing_activity_ids')
    def _compute_allowed_parent_ids(self):
        for activity in self:
            if activity.trigger_type == 'activity':
                activity.allowed_parent_ids = activity.campaign_id.marketing_activity_ids.filtered(
                    lambda parent_id: parent_id.ids != activity.ids)
            elif activity.trigger_category:
                activity.allowed_parent_ids = activity.campaign_id.marketing_activity_ids.filtered(
                    lambda parent_id: parent_id.ids != activity.ids and parent_id.activity_type == activity.trigger_category)
            else:
                activity.allowed_parent_ids = False

    @api.depends('trigger_type')
    def _compute_trigger_category(self):
        for activity in self:
            if activity.trigger_type in ['mail_open', 'mail_not_open', 'mail_reply', 'mail_not_reply',
                                         'mail_click', 'mail_not_click', 'mail_bounce']:
                activity.trigger_category = 'email'
            else:
                activity.trigger_category = False

    @api.depends('activity_type', 'trace_ids')
    def _compute_statistics(self):
        # Fix after ORM-pocalyspe : Update in any case, otherwise, None to some values (crash)
        self.update({
            'total_bounce': 0, 'total_reply': 0, 'total_sent': 0,
            'rejected': 0, 'total_click': 0, 'processed': 0, 'total_open': 0,
        })
        if self.ids:
            activity_data = {activity._origin.id: {} for activity in self}
            for stat in self._get_full_statistics():
                activity_data[stat.pop('activity_id')].update(stat)
            for activity in self:
                activity.update(activity_data[activity._origin.id])

    @api.depends('activity_type', 'trace_ids')
    def _compute_statistics_graph_data(self):
        if not self.ids:
            date_range = [date.today() - timedelta(days=d) for d in range(0, 15)]
            date_range.reverse()
            default_values = [{'x': date_item.strftime('%d %b'), 'y': 0} for date_item in date_range]
            self.statistics_graph_data = json.dumps([
                {'points': default_values, 'label': _('Success'), 'color': '#21B799'},
                {'points': default_values, 'label': _('Rejected'), 'color': '#d9534f'}])
        else:
            activity_data = {activity._origin.id: {} for activity in self}
            for act_id, graph_data in self._get_graph_statistics().items():
                activity_data[act_id]['statistics_graph_data'] = json.dumps(graph_data)
            for activity in self:
                activity.update(activity_data[activity._origin.id])

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if any(not activity._check_recursion() for activity in self):
            raise ValidationError(_("Error! You can't create recursive hierarchy of Activity."))

    @api.model
    def create(self, values):
        campaign_id = values.get('campaign_id')
        if not campaign_id:
            campaign_id = self.default_get(['campaign_id'])['campaign_id']
        values['require_sync'] = self.env['marketing.campaign'].browse(campaign_id).state == 'running'
        return super(MarketingActivity, self).create(values)

    def write(self, values):
        if any(field in values.keys() for field in ('interval_number', 'interval_type')):
            values['require_sync'] = True
        return super(MarketingActivity, self).write(values)

    def _get_full_statistics(self):
        self.env.cr.execute("""
            SELECT
                trace.activity_id,
                COUNT(CASE WHEN stat.sent IS NOT NULL THEN 1 ELSE null END) AS total_sent,
                COUNT(CASE WHEN stat.clicked IS NOT NULL THEN 1 ELSE null END) AS total_click,
                COUNT(CASE WHEN stat.replied IS NOT NULL THEN 1 ELSE null END) AS total_reply,
                COUNT(CASE WHEN stat.opened IS NOT NULL THEN 1 ELSE null END) AS total_open,
                COUNT(CASE WHEN stat.bounced IS NOT NULL THEN 1 ELSE null END) AS total_bounce,
                COUNT(CASE WHEN trace.state = 'processed' THEN 1 ELSE null END) AS processed,
                COUNT(CASE WHEN trace.state = 'rejected' THEN 1 ELSE null END) AS rejected
            FROM
                marketing_trace AS trace
            LEFT JOIN
                mailing_trace AS stat
                ON (stat.marketing_trace_id = trace.id)
            JOIN
                marketing_participant AS part
                ON (trace.participant_id = part.id)
            WHERE
                (part.is_test = false or part.is_test IS NULL) AND
                trace.activity_id IN %s
            GROUP BY
                trace.activity_id;
        """, (tuple(self.ids), ))
        return self.env.cr.dictfetchall()

    def _get_graph_statistics(self):
        """ Compute activities statistics based on their traces state for the last fortnight """
        past_date = (Datetime.from_string(Datetime.now()) + timedelta(days=-14)).strftime('%Y-%m-%d 00:00:00')
        stat_map = {}
        base = date.today() + timedelta(days=-14)
        date_range = [base + timedelta(days=d) for d in range(0, 15)]

        self.env.cr.execute("""
            SELECT
                activity.id AS activity_id,
                trace.schedule_date::date AS dt,
                count(*) AS total,
                trace.state
            FROM
                marketing_trace AS trace
            JOIN
                marketing_activity AS activity
                ON (activity.id = trace.activity_id)
            WHERE
                activity.id IN %s AND
                trace.schedule_date >= %s AND
                (trace.is_test = false or trace.is_test IS NULL)
            GROUP BY activity.id , dt, trace.state
            ORDER BY dt;
        """, (tuple(self.ids), past_date))

        for stat in self.env.cr.dictfetchall():
            stat_map[(stat['activity_id'], stat['dt'], stat['state'])] = stat['total']
        graph_data = {}
        for activity in self:
            success = []
            rejected = []
            for i in date_range:
                x = i.strftime('%d %b')
                success.append({
                    'x': x,
                    'y': stat_map.get((activity._origin.id, i, 'processed'), 0)
                })
                rejected.append({
                    'x': x,
                    'y': stat_map.get((activity._origin.id, i, 'rejected'), 0)
                })
            graph_data[activity._origin.id] = [
                {'points': success, 'label': _('Success'), 'color': '#21B799'},
                {'points': rejected, 'label': _('Rejected'), 'color': '#d9534f'}
            ]
        return graph_data

    def execute(self, domain=None):
        # auto-commit except in testing mode
        auto_commit = not getattr(threading.currentThread(), 'testing', False)
        trace_domain = [
            ('schedule_date', '<=', Datetime.now()),
            ('state', '=', 'scheduled'),
            ('activity_id', 'in', self.ids),
            ('participant_id.state', '=', 'running'),
        ]
        if domain:
            trace_domain += domain

        traces = self.env['marketing.trace'].search(trace_domain)

        # organize traces by activity
        trace_to_activities = dict()
        for trace in traces:
            if trace.activity_id not in trace_to_activities:
                trace_to_activities[trace.activity_id] = trace
            else:
                trace_to_activities[trace.activity_id] |= trace

        # execute activity on their traces
        BATCH_SIZE = 500  # same batch size as the MailComposer
        for activity, traces in trace_to_activities.items():
            for traces_batch in (traces[i:i + BATCH_SIZE] for i in range(0, len(traces), BATCH_SIZE)):
                activity.execute_on_traces(traces_batch)
                if auto_commit:
                    self.env.cr.commit()

    def execute_on_traces(self, traces):
        """ Execute current activity on given traces.

        :param traces: record set of traces on which the activity should run
        """
        self.ensure_one()
        new_traces = self.env['marketing.trace']

        if self.validity_duration:
            duration = relativedelta(**{self.validity_duration_type: self.validity_duration_number})
            invalid_traces = traces.filtered(
                lambda trace: not trace.schedule_date or trace.schedule_date + duration < datetime.now()
            )
            invalid_traces.action_cancel()
            traces = traces - invalid_traces

        # Filter traces not fitting the activity filter and whose record has been deleted
        if self.domain:
            rec_domain = expression.AND([literal_eval(self.campaign_id.domain), literal_eval(self.domain)])
        else:
            rec_domain = literal_eval(self.campaign_id.filter)
        if rec_domain:
            rec_valid = self.env[self.model_name].search(rec_domain)
            rec_ids_domain = set(rec_valid.ids)

            traces_allowed = traces.filtered(lambda trace: trace.res_id in rec_ids_domain or trace.is_test)
            traces_rejected = traces.filtered(lambda trace: trace.res_id not in rec_ids_domain and not trace.is_test)  # either rejected, either deleted record
        else:
            traces_allowed = traces
            traces_rejected = self.env['marketing.trace']

        if traces_allowed:
            activity_method = getattr(self, '_execute_%s' % (self.activity_type))
            activity_method(traces_allowed)
            new_traces |= self._generate_children_traces(traces_allowed)
            traces.mapped('participant_id').check_completed()

        if traces_rejected:
            traces_rejected.write({
                'state': 'rejected',
                'state_msg': _('Rejected by activity filter or record deleted / archived')
            })
            traces_rejected.mapped('participant_id').check_completed()

        return new_traces

    def _execute_action(self, traces):
        if not self.server_action_id:
            return False

        # Do a loop here because we have to try / catch each execution separately to ensure other traces are executed
        # and proper state message stored
        traces_ok = self.env['marketing.trace']
        for trace in traces:
            action = self.server_action_id.with_context(
                active_model=self.model_name,
                active_ids=[trace.res_id],
                active_id=trace.res_id,
            )
            try:
                action.run()
            except Exception as e:
                _logger.warning('Marketing Automation: activity <%s> encountered server action issue %s', self.id, str(e), exc_info=True)
                trace.write({
                    'state': 'error',
                    'schedule_date': Datetime.now(),
                    'state_msg': _('Exception in server action: %s', str)(e),
                })
            else:
                traces_ok |= trace

        # Update status
        traces_ok.write({
            'state': 'processed',
            'schedule_date': Datetime.now(),
        })
        return True

    def _execute_email(self, traces):
        res_ids = [r for r in set(traces.mapped('res_id'))]

        mailing = self.mass_mailing_id.with_context(
            default_marketing_activity_id=self.ids[0],
            active_ids=res_ids,
        )

        # we only allow to continue if the user has sufficient rights, as a sudo() follows
        if not self.env.is_superuser() and not self.user_has_groups('marketing_automation.group_marketing_automation_user'):
            raise AccessError(_('To use this feature you should be an administrator or belong to the marketing automation group.'))
        try:
            mailing.sudo().action_send_mail(res_ids)
        except Exception as e:
            _logger.warning('Marketing Automation: activity <%s> encountered mass mailing issue %s', self.id, str(e), exc_info=True)
            traces.write({
                'state': 'error',
                'schedule_date': Datetime.now(),
                'state_msg': _('Exception in mass mailing: %s', str)(e),
            })
        else:
            failed_stats = self.env['mailing.trace'].sudo().search([
                ('marketing_trace_id', 'in', traces.ids),
                '|', ('exception', '!=', False), ('ignored', '!=', False)])
            ignored_doc_ids = [stat.res_id for stat in failed_stats if stat.exception]
            error_doc_ids = [stat.res_id for stat in failed_stats if stat.ignored]

            processed_traces = traces
            ignored_traces = traces.filtered(lambda trace: trace.res_id in ignored_doc_ids)
            error_traces = traces.filtered(lambda trace: trace.res_id in error_doc_ids)

            if ignored_traces:
                ignored_traces.write({
                    'state': 'canceled',
                    'schedule_date': Datetime.now(),
                    'state_msg': _('Email ignored')
                })
                processed_traces = processed_traces - ignored_traces
            if error_traces:
                error_traces.write({
                    'state': 'error',
                    'schedule_date': Datetime.now(),
                    'state_msg': _('Email failed')
                })
                processed_traces = processed_traces - error_traces
            if processed_traces:
                processed_traces.write({
                    'state': 'processed',
                    'schedule_date': Datetime.now(),
                })
        return True

    def _generate_children_traces(self, traces):
        """Generate child traces for child activities and compute their schedule date except for mail_open,
        mail_click, mail_reply, mail_bounce which are computed when processing the mail event """
        child_traces = self.env['marketing.trace']
        for activity in self.child_ids:
            activity_offset = relativedelta(**{activity.interval_type: activity.interval_number})

            for trace in traces:
                vals = {
                    'parent_id': trace.id,
                    'participant_id': trace.participant_id.id,
                    'activity_id': activity.id
                }
                if activity.trigger_type in ['activity', 'mail_not_open', 'mail_not_click', 'mail_not_reply']:
                    vals['schedule_date'] = Datetime.from_string(trace.schedule_date) + activity_offset
                child_traces |= child_traces.create(vals)

        return child_traces

    def action_view_sent(self):
        return self._action_view_documents_filtered('sent')

    def action_view_replied(self):
        return self._action_view_documents_filtered('replied')

    def action_view_clicked(self):
        return self._action_view_documents_filtered('clicked')

    def action_view_bounced(self):
        return self._action_view_documents_filtered('bounced')

    def _action_view_documents_filtered(self, view_filter):
        if not self.mass_mailing_id:  # Only available for mass mailing
            return False
        action = self.env["ir.actions.actions"]._for_xml_id("marketing_automation.marketing_participants_action_mail")
        participant_ids = self.trace_ids.filtered(lambda stat: stat[view_filter]).mapped("participant_id").ids
        action.update({
            'display_name': _('Participants of %s (%s)') % (self.name, view_filter),
            'domain': [('id', 'in', participant_ids)],
            'context': dict(self._context, create=False)
        })
        return action
