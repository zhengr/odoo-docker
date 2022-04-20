# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from contextlib import contextmanager
from unittest.mock import patch
from dateutil.relativedelta import relativedelta
from datetime import datetime

from odoo import fields
from odoo.tests.common import SavepointCase

NOW = datetime(2018, 10, 10, 9, 18)
NOW2 = datetime(2019, 1, 8, 9, 0)


class HelpdeskSLA(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(HelpdeskSLA, cls).setUpClass()

        # we create a helpdesk user and a manager
        Users = cls.env['res.users'].with_context(tracking_disable=True)
        cls.main_company_id = cls.env.ref('base.main_company').id
        cls.helpdesk_manager = Users.create({
            'company_id': cls.main_company_id,
            'name': 'Helpdesk Manager',
            'login': 'hm',
            'email': 'hm@example.com',
            'groups_id': [(6, 0, [cls.env.ref('helpdesk.group_helpdesk_manager').id])]
        })
        cls.helpdesk_user = Users.create({
            'company_id': cls.main_company_id,
            'name': 'Helpdesk User',
            'login': 'hu',
            'email': 'hu@example.com',
            'groups_id': [(6, 0, [cls.env.ref('helpdesk.group_helpdesk_user').id])]
        })
        # the manager defines a team for our tests (the .sudo() at the end is to avoid potential uid problems)
        cls.test_team = cls.env['helpdesk.team'].with_user(cls.helpdesk_manager).create({
            'name': 'Test Team',
            'use_sla': True
        }).sudo()
        # He then defines its stages
        stage_as_manager = cls.env['helpdesk.stage'].with_user(cls.helpdesk_manager)
        cls.stage_new = stage_as_manager.create({
            'name': 'New',
            'sequence': 10,
            'team_ids': [(4, cls.test_team.id, 0)],
            'is_close': False,
        })
        cls.stage_progress = stage_as_manager.create({
            'name': 'In Progress',
            'sequence': 20,
            'team_ids': [(4, cls.test_team.id, 0)],
            'is_close': False,
        })
        cls.stage_wait = stage_as_manager.create({
            'name': 'Waiting',
            'sequence': 25,
            'team_ids': [(4, cls.test_team.id, 0)],
            'is_close': False,
        })
        cls.stage_done = stage_as_manager.create({
            'name': 'Done',
            'sequence': 30,
            'team_ids': [(4, cls.test_team.id, 0)],
            'is_close': True,
        })
        cls.stage_cancel = stage_as_manager.create({
            'name': 'Cancelled',
            'sequence': 40,
            'team_ids': [(4, cls.test_team.id, 0)],
            'is_close': True,
        })

        cls.tag_vip = cls.env['helpdesk.tag'].with_user(cls.helpdesk_manager).create({'name': 'VIP'})
        cls.tag_urgent = cls.env['helpdesk.tag'].with_user(cls.helpdesk_manager).create({'name': 'Urgent'})
        cls.tag_freeze = cls.env['helpdesk.tag'].with_user(cls.helpdesk_manager).create({'name': 'Freeze'})

        cls.sla = cls.env['helpdesk.sla'].create({
            'name': 'SLA',
            'team_id': cls.test_team.id,
            'time_days': 1,
            'time_hours': 24,
            'stage_id': cls.stage_progress.id,
        })
        cls.sla_2 = cls.env['helpdesk.sla'].create({
            'name': 'SLA done stage with freeze time',
            'team_id': cls.test_team.id,
            'time_days': 1,
            'time_hours': 2,
            'time_minutes': 2,
            'tag_ids': [(4, cls.tag_freeze.id)],
            'exclude_stage_ids': cls.stage_wait.ids,
            'stage_id': cls.stage_done.id,
        })
        cls.sla_assigning_1 = cls.env['helpdesk.sla'].create({
            'name': 'SLA assigning no stage',
            'team_id': cls.test_team.id,
            'time_hours': 1,
            'target_type': 'assigning'
        })

        cls.sla_assigning_2 = cls.env['helpdesk.sla'].create({
            'name': 'SLA assigning new stage',
            'team_id': cls.test_team.id,
            'time_hours': 1,
            'stage_id': cls.stage_new.id,
            'target_type': 'assigning'
        })

        cls.sla_assigning_3 = cls.env['helpdesk.sla'].create({
            'name': 'SLA assigning progress stage',
            'team_id': cls.test_team.id,
            'time_hours': 1,
            'stage_id': cls.stage_progress.id,
            'target_type': 'assigning'
        })

        cls.sla_assigning_4 = cls.env['helpdesk.sla'].create({
            'name': 'SLA assigning done stage',
            'team_id': cls.test_team.id,
            'time_hours': 1,
            'stage_id': cls.stage_done.id,
            'target_type': 'assigning'
        })

        # He also creates a ticket types for Question and Issue
        cls.type_question = cls.env['helpdesk.ticket.type'].with_user(cls.helpdesk_manager).create({
            'name': 'Question_test',
        }).sudo()
        cls.type_issue = cls.env['helpdesk.ticket.type'].with_user(cls.helpdesk_manager).create({
            'name': 'Issue_test',
        }).sudo()

    def _utils_set_create_date(self, records, date_str, ticket_to_update=False):
        """ This method is a hack in order to be able to define/redefine the create_date
            of the any recordset. This is done in SQL because ORM does not allow to write
            onto the create_date field.
            :param records: recordset of any odoo models
        """
        query = """
            UPDATE %s
            SET create_date = %%s
            WHERE id IN %%s
        """ % (records._table,)
        self.env.cr.execute(query, (date_str, tuple(records.ids)))

        records.invalidate_cache()

        if ticket_to_update:
            ticket_to_update.sla_status_ids._compute_deadline()

    @contextmanager
    def _ticket_patch_now(self, datetime_str):
        datetime_now_old = getattr(fields.Datetime, 'now')
        datetime_today_old = getattr(fields.Datetime, 'today')

        def new_now():
            return fields.Datetime.from_string(datetime_str)

        def new_today():
            return fields.Datetime.from_string(datetime_str).replace(hour=0, minute=0, second=0)

        try:
            setattr(fields.Datetime, 'now', new_now)
            setattr(fields.Datetime, 'today', new_today)

            yield
        finally:
            # back
            setattr(fields.Datetime, 'now', datetime_now_old)
            setattr(fields.Datetime, 'today', datetime_today_old)

    def create_ticket(self, *arg, **kwargs):
        default_values = {
            'name': "Help me",
            'team_id': self.test_team.id,
            'tag_ids': [(4, self.tag_urgent.id)],
            'stage_id': self.stage_new.id,
        }
        if 'tag_ids' in kwargs:
            # from recordset to ORM command
            kwargs['tag_ids'] = [(6, False, [tag.id for tag in kwargs['tag_ids']])]
        values = dict(default_values, **kwargs)
        return self.env['helpdesk.ticket'].create(values)

    def test_sla_no_tag(self):
        """ SLA without tag should apply to all tickets """
        self.sla.tag_ids = [(5,)]
        ticket = self.create_ticket(tag_ids=self.tag_urgent)
        self.assertEqual(ticket.sla_status_ids.filtered(lambda sla: sla.target_type != 'assigning').sla_id, self.sla, "SLA should have been applied")

    def test_sla_single_tag(self):
        self.sla.tag_ids = [(4, self.tag_urgent.id)]
        ticket = self.create_ticket(tag_ids=self.tag_urgent)
        self.assertEqual(ticket.sla_status_ids.filtered(lambda sla: sla.target_type != 'assigning').sla_id, self.sla, "SLA should have been applied")

    def test_sla_multiple_tags(self):
        self.sla.tag_ids = [(6, False, (self.tag_urgent | self.tag_vip).ids)]
        ticket = self.create_ticket(tag_ids=self.tag_urgent)
        self.assertFalse(ticket.sla_status_ids.filtered(lambda sla: sla.target_type != 'assigning'), "SLA should not have been applied yet")
        ticket.tag_ids = [(4, self.tag_vip.id)]
        self.assertEqual(ticket.sla_status_ids.filtered(lambda sla: sla.target_type != 'assigning').sla_id, self.sla, "SLA should have been applied")

    def test_sla_tag_and_ticket_type(self):
        self.sla.tag_ids = [(6, False, self.tag_urgent.ids)]
        self.sla.ticket_type_id = self.type_question
        ticket = self.create_ticket(tag_ids=self.tag_urgent)
        self.assertFalse(ticket.sla_status_ids.filtered(lambda sla: sla.target_type != 'assigning'), "SLA should not have been applied yet")
        ticket.ticket_type_id = self.type_question
        self.assertEqual(ticket.sla_status_ids.filtered(lambda sla: sla.target_type != 'assigning').sla_id, self.sla, "SLA should have been applied")

    def test_sla_remove_tag(self):
        self.sla.tag_ids = [(6, False, (self.tag_urgent | self.tag_vip).ids)]
        ticket = self.create_ticket(tag_ids=self.tag_urgent | self.tag_vip)
        self.assertEqual(ticket.sla_status_ids.filtered(lambda sla: sla.target_type != 'assigning').sla_id, self.sla, "SLA should have been applied")
        ticket.tag_ids = [(5,)]  # Remove all tags
        self.assertFalse(ticket.sla_status_ids.filtered(lambda sla: sla.target_type != 'assigning'), "SLA should no longer apply")

    @patch.object(fields.Datetime, 'now', lambda: NOW2)
    def test_sla_waiting(self):
        ticket = self.create_ticket(tag_ids=self.tag_freeze)
        self._utils_set_create_date(ticket, '2019-01-08 9:00:00', ticket)
        status = ticket.sla_status_ids.filtered(lambda sla: sla.sla_id.id == self.sla_2.id)
        self.assertEqual(status.deadline, datetime(2019, 1, 9, 12, 2, 0), 'No waiting time, deadline = creation date + 1 day + 2 hours + 2 minutes')

        ticket.write({'stage_id': self.stage_progress.id})
        initial_values = {ticket.id: {'stage_id': self.stage_new}}
        ticket.message_track(['stage_id'], initial_values)
        self._utils_set_create_date(ticket.message_ids.tracking_value_ids, '2019-01-08 11:09:50', ticket)
        self.assertEqual(status.deadline, datetime(2019, 1, 9, 12, 2, 0), 'No waiting time, deadline = creation date + 1 day + 2 hours + 2 minutes')

        # We are in waiting stage, they are no more deadline.
        ticket.write({'stage_id': self.stage_wait.id})
        initial_values = {ticket.id: {'stage_id': self.stage_progress}}
        ticket.message_track(['stage_id'], initial_values)
        self._utils_set_create_date(ticket.message_ids.tracking_value_ids[0], '2019-01-08 12:15:00', ticket)
        self.assertFalse(status.deadline, 'In waiting stage: no more deadline')

        #  We have a response of our customer, the ticket switch to in progress stage (outside working hours)
        ticket.write({'stage_id': self.stage_progress.id})
        initial_values = {ticket.id: {'stage_id': self.stage_wait}}
        ticket.message_track(['stage_id'], initial_values)
        self._utils_set_create_date(ticket.message_ids.tracking_value_ids[0], '2019-01-12 10:35:58', ticket)
        # waiting time = 3 full working days 9 - 10 - 11 January (12 doesn't count as it's Saturday)
        #  + (8 January) 12:15:00 -> 16:00:00 (end of working day) 3,75 hours
        # Old deadline = '2019-01-09 12:02:00'
        # New: '2019-01-09 12:02:00' + 3 days (waiting) + 2 days (weekend) + 3.75 hours (waiting) = '2019-01-14 15:47:00'
        self.assertEqual(status.deadline, datetime(2019, 1, 14, 15, 47), 'We have waiting time: deadline = old_deadline + 3 full working days (waiting) + 3.75 hours (waiting) + 2 days (weekend)')

        ticket.write({'stage_id': self.stage_wait.id})
        initial_values = {ticket.id: {'stage_id': self.stage_progress}}
        ticket.message_track(['stage_id'], initial_values)
        self._utils_set_create_date(ticket.message_ids.tracking_value_ids[0], '2019-01-14 15:30:00', ticket)
        self.assertFalse(status.deadline, 'In waiting stage: no more deadline')

        # We need to patch now with a new value as it will be used to compute freezed time.
        with patch.object(fields.Datetime, 'now', lambda: datetime(2019, 1, 16, 15, 0)):
            ticket.write({'stage_id': self.stage_done.id})
            initial_values = {ticket.id: {'stage_id': self.stage_wait}}
            ticket.message_track(['stage_id'], initial_values)
            self._utils_set_create_date(ticket.message_ids.tracking_value_ids[0], '2019-01-16 15:00:00', ticket)
            self.assertEqual(status.deadline, datetime(2019, 1, 16, 15, 17), 'We have waiting time: deadline = old_deadline +  7.5 hours (waiting)')

    def test_sla_assigning(self):
        ticket = self.create_ticket()

        status_1 = ticket.sla_status_ids.filtered(lambda sla: sla.sla_id.id == self.sla_assigning_1.id)
        status_2 = ticket.sla_status_ids.filtered(lambda sla: sla.sla_id.id == self.sla_assigning_2.id)
        status_3 = ticket.sla_status_ids.filtered(lambda sla: sla.sla_id.id == self.sla_assigning_3.id)
        status_4 = ticket.sla_status_ids.filtered(lambda sla: sla.sla_id.id == self.sla_assigning_4.id)

        self.assertFalse(status_1.reached_datetime, "SLA status 1: reached not his target")
        self.assertFalse(status_2.reached_datetime, "SLA status 2: reached not his target")
        self.assertFalse(status_3.reached_datetime, "SLA status 3: reached not his target")
        self.assertFalse(status_4.reached_datetime, "SLA status 4: reached not his target")
        self.assertTrue(status_1.deadline, "SLA status 1: has deadline")
        self.assertTrue(status_2.deadline, "SLA status 2: has deadline")
        self.assertFalse(status_3.deadline, "SLA status 3: hasn't deadline")
        self.assertFalse(status_4.deadline, "SLA status 4: hasn't deadline")

        ticket.write({'user_id': self.helpdesk_user.id})

        self.assertTrue(status_1.reached_datetime, "SLA status 1: reached his target")
        self.assertTrue(status_2.reached_datetime, "SLA status 2: reached his target")
        self.assertFalse(status_3.reached_datetime, "SLA status 3: reached not his target")
        self.assertTrue(status_1.deadline, "SLA status 1: has deadline")
        self.assertTrue(status_2.deadline, "SLA status 2: has deadline")
        self.assertFalse(status_3.deadline, "SLA status 3: hasn't deadline")

        ticket.write({'stage_id': self.stage_progress.id})

        self.assertTrue(status_1.reached_datetime, "SLA status 1: reached his target")
        self.assertTrue(status_2.reached_datetime, "SLA status 2: reached his target")
        self.assertTrue(status_3.reached_datetime, "SLA status 3: reached his target")
        self.assertTrue(status_1.deadline, "SLA status 1: has deadline")
        self.assertTrue(status_2.deadline, "SLA status 2: has deadline")
        self.assertTrue(status_3.deadline, "SLA status 3: has deadline")

        ticket.write({'user_id': False})

        self.assertTrue(status_1.reached_datetime, "SLA status 1: reached his target")
        self.assertTrue(status_2.reached_datetime, "SLA status 2: reached his target")
        self.assertTrue(status_3.reached_datetime, "SLA status 3: reached his target")
        self.assertFalse(status_4.reached_datetime, "SLA status 4: reached not his target")
        self.assertTrue(status_1.deadline, "SLA status 1: has deadline")
        self.assertTrue(status_2.deadline, "SLA status 2: has deadline")
        self.assertTrue(status_3.deadline, "SLA status 3: has deadline")
        self.assertFalse(status_4.deadline, "SLA status 4: hasn't deadline")

        ticket.write({'stage_id': self.stage_done.id})

        self.assertTrue(status_3.reached_datetime, "SLA status 3: reached his target")
        self.assertFalse(status_4.reached_datetime, "SLA status 4: reached not his target")
        self.assertTrue(status_3.deadline, "SLA status 3: has deadline")
        self.assertTrue(status_4.deadline, "SLA status 4: has deadline")

        ticket.write({'user_id': self.helpdesk_user.id})

        self.assertTrue(status_4.reached_datetime, "SLA status 4: reached his target")

    def test_sla_assigning_skip_step(self):
        ticket = self.create_ticket()

        status_1 = ticket.sla_status_ids.filtered(lambda sla: sla.sla_id.id == self.sla_assigning_1.id)
        status_2 = ticket.sla_status_ids.filtered(lambda sla: sla.sla_id.id == self.sla_assigning_2.id)

        self.assertTrue(status_2.deadline, "SLA status 2: has deadline")

        ticket.write({'stage_id': self.stage_progress.id})

        self.assertFalse(status_2.deadline, "SLA status 2: has no more deadline")
        self.assertFalse(status_2.reached_datetime, "SLA status 2: reached not his target")

        ticket.write({'user_id': self.helpdesk_user.id})

        self.assertTrue(status_1.reached_datetime, "SLA status 1: reached his target")

    @patch.object(fields.Date, 'today', lambda: NOW.date())
    @patch.object(fields.Datetime, 'today', lambda: NOW.replace(hour=0, minute=0, second=0))
    @patch.object(fields.Datetime, 'now', lambda: NOW)
    def test_failed_tickets(self):
        self.sla.time_days = 0
        self.sla.time_hours = 3
        # Failed ticket
        failed_ticket = self.create_ticket(user_id=self.env.user.id, create_date=NOW - relativedelta(hours=3, minutes=2))

        # Not failed ticket
        ticket = self.create_ticket(user_id=self.env.user.id, create_date=NOW - relativedelta(hours=2, minutes=2))

        data = self.env['helpdesk.team'].retrieve_dashboard()
        self.assertEqual(data['my_all']['count'], 2, "There should be 2 tickets")
        self.assertEqual(data['my_all']['failed'], 1, "There should be 1 failed ticket")
