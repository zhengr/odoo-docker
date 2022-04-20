# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details
from datetime import datetime
from dateutil.relativedelta import relativedelta

from .common import TestCommonPlanning

class TestPlanning(TestCommonPlanning):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpEmployees()
        cls.slot = cls.env['planning.slot'].create({
            'start_datetime': datetime(2019, 6, 27, 8, 0, 0),
            'end_datetime': datetime(2019, 6, 27, 18, 0, 0),
        })
        cls.template = cls.env['planning.slot.template'].create({
            'start_time': 11,
            'duration': 4,
        })

    def test_allocated_hours_defaults(self):
        self.assertEqual(self.slot.allocated_hours, 10, "It should have the default value")
        self.assertEqual(self.slot.allocated_percentage, 100, "It should have the default value")

    def test_change_percentage(self):
        self.slot.allocated_percentage = 60
        self.assertEqual(self.slot.allocated_hours, 6, "It should 60%% of original hours")

    def test_change_hours_more(self):
        self.slot.allocated_hours = 15
        self.assertEqual(self.slot.allocated_percentage, 150)

    def test_change_hours_less(self):
        self.slot.allocated_hours = 5
        self.assertEqual(self.slot.allocated_percentage, 50)

    def test_change_start(self):
        self.slot.start_datetime += relativedelta(hours=2)
        self.assertEqual(self.slot.allocated_percentage, 100, "It should still be 100%")
        self.assertEqual(self.slot.allocated_hours, 8, "It should decreased by 2 hours")

    def test_change_start_partial(self):
        self.slot.allocated_percentage = 80
        self.slot.start_datetime += relativedelta(hours=2)
        self.slot.flush()
        self.slot.invalidate_cache()
        self.assertEqual(self.slot.allocated_hours, 8 * 0.8, "It should be decreased by 2 hours and percentage applied")
        self.assertEqual(self.slot.allocated_percentage, 80, "It should still be 80%")

    def test_change_end(self):
        self.slot.end_datetime -= relativedelta(hours=2)
        self.assertEqual(self.slot.allocated_percentage, 100, "It should still be 100%")
        self.assertEqual(self.slot.allocated_hours, 8, "It should decreased by 2 hours")

    def test_set_template(self):
        self.env.user.tz = 'Europe/Brussels'
        self.slot.template_id = self.template
        self.assertEqual(self.slot.start_datetime, datetime(2019, 6, 27, 9, 0), 'It should set time from template, in user timezone (11am CET -> 9am UTC)')

    def test_change_employee_with_template(self):
        self.slot.template_id = self.template
        self.slot.flush()

        # simulate public user (no tz)
        self.env.user.tz = False
        self.slot.employee_id = self.employee_janice.id
        self.assertEqual(self.slot.template_id, self.template, 'It should keep the template')
        self.assertEqual(self.slot.start_datetime, datetime(2019, 6, 27, 15, 0), 'It should adjust for employee timezone: 11am EDT -> 3pm UTC')

    def test_unassign_employee_with_template(self):
        # we are going to put everybody in EDT, because if the employee has a different timezone from the company this workflow does not work.
        self.env.user.tz = 'America/New_York'
        self.env.user.company_id.resource_calendar_id.tz = 'America/New_York'
        self.slot.template_id = self.template
        self.slot.flush()
        self.assertEqual(self.slot.start_datetime, datetime(2019, 6, 27, 15, 0), 'It should set time from template, in user timezone (11am EDT -> 3pm UTC)')

        # simulate public user (no tz)
        self.env.user.tz = False
        self.slot.employee_id = self.employee_janice.id
        self.slot.flush()
        self.assertEqual(self.slot.start_datetime, datetime(2019, 6, 27, 15, 0), 'It should adjust to employee timezone')

        self.slot.employee_id = None
        self.assertEqual(self.slot.template_id, self.template, 'It should keep the template')
        self.assertEqual(self.slot.start_datetime, datetime(2019, 6, 27, 15, 0), 'It should reset to company calendar timezone: 11am EDT -> 3pm UTC')

    def test_compute_overlap_count(self):
        self.slot_6_2 = self.env['planning.slot'].create({
            'employee_id': self.employee_bert.id,
            'start_datetime': datetime(2019, 6, 2, 8, 0),
            'end_datetime': datetime(2019, 6, 2, 17, 0),
        })
        self.slot_6_3 = self.env['planning.slot'].create({
            'employee_id': self.employee_bert.id,
            'start_datetime': datetime(2019, 6, 3, 8, 0),
            'end_datetime': datetime(2019, 6, 3, 17, 0),
        })
        self.env['planning.slot'].create({
            'employee_id': self.employee_bert.id,
            'start_datetime': datetime(2019, 6, 2, 10, 0),
            'end_datetime': datetime(2019, 6, 2, 12, 0),
        })
        self.env['planning.slot'].create({
            'employee_id': self.employee_bert.id,
            'start_datetime': datetime(2019, 6, 2, 16, 0),
            'end_datetime': datetime(2019, 6, 2, 18, 0),
        })
        self.env['planning.slot'].create({
            'employee_id': self.employee_bert.id,
            'start_datetime': datetime(2019, 6, 2, 18, 0),
            'end_datetime': datetime(2019, 6, 2, 20, 0),
        })
        self.assertEqual(2, self.slot_6_2.overlap_slot_count, '2 slots overlap')
        self.assertEqual(0, self.slot_6_3.overlap_slot_count, 'no slot overlap')
