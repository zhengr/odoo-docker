# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details

from odoo.addons.industry_fsm.tests.common import TestFsmFlowCommon
from dateutil.relativedelta import relativedelta
from datetime import datetime


class TestFsmFlow(TestFsmFlowCommon):

    def test_planning_overlap(self):
        task_A = self.env['project.task'].create({
            'name': 'Fsm task 1',
            'user_id': self.project_user.id,
            'project_id': self.fsm_project.id,
            'planned_date_begin': datetime.now(),
            'planned_date_end': datetime.now() + relativedelta(hours=4)
        })
        task_B = self.env['project.task'].create({
            'name': 'Fsm task 2',
            'user_id': self.project_user.id,
            'project_id': self.fsm_project.id,
            'planned_date_begin': datetime.now() + relativedelta(hours=2),
            'planned_date_end': datetime.now() + relativedelta(hours=6)
        })
        task_C = self.env['project.task'].create({
            'name': 'Fsm task 2',
            'user_id': self.project_user.id,
            'project_id': self.fsm_project.id,
            'planned_date_begin': datetime.now() + relativedelta(hours=5),
            'planned_date_end': datetime.now() + relativedelta(hours=7)
        })
        task_D = self.env['project.task'].create({
            'name': 'Fsm task 2',
            'user_id': self.project_user.id,
            'project_id': self.fsm_project.id,
            'planned_date_begin': datetime.now() + relativedelta(hours=8),
            'planned_date_end': datetime.now() + relativedelta(hours=9)
        })
        self.assertEqual(task_A.planning_overlap, 1, "One task should be overlapping with task_A")
        self.assertEqual(task_B.planning_overlap, 2, "Two tasks should be overlapping with task_B")
        self.assertFalse(task_D.planning_overlap, "No task should be overlapping with task_D")
