# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details
from datetime import datetime

from odoo.tests.common import Form, new_test_user
from .common import TestCommonPlanning


class TestPlanningForm(TestCommonPlanning):

    def test_planning_no_employee_no_company(self):
      """ test multi day slot without calendar (no employee nor company) """
      with Form(self.env['planning.slot']) as slot:
        start, end = datetime(2020, 1, 1, 8, 0), datetime(2020, 1, 11, 18, 0)
        slot.start_datetime = start
        slot.end_datetime = end
        slot.employee_id = self.env['hr.employee']
        slot.company_id = self.env['res.company']
        slot.allocated_percentage = 100
        self.assertEqual(slot.allocated_hours, (end - start).total_seconds() / (60 * 60))

    def test_planning_default_times_timezoned(self):
      """ User with timezone A creates a slot for employee in timezone B """
      employee =  self.env['hr.employee'].create({
        'name': "John",
        'tz': 'Europe/Brussels',
      })
      user = new_test_user(self.env, "Johnny Testing", tz='Asia/Colombo', groups='planning.group_planning_manager')
      start, end = datetime(2020, 1, 1, 8, 0), datetime(2020, 1, 11, 18, 0)
      context = dict(
        default_employee_id=employee.id,
        default_start_datetime=start,
        default_end_datetime=end,
      )
      with Form(self.env['planning.slot'].with_user(user).with_context(context)) as slot:
        # until we find a proper way to do it:
        self.assertEqual(slot.start_datetime, start, "It should not have been adjusted to the employee's calendar")
        self.assertEqual(slot.end_datetime, end, "It should not have been adjusted to the employee's calendar")
