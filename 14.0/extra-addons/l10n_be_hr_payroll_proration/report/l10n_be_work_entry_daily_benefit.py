# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools
from psycopg2 import sql


class l10nBeWorkEntryDailyBenefitReport(models.Model):
    """Generates a list of combination of dates, benefit name and employee_id.
       The list is created in accordance with:
       * The work entries currently in the system and the benefits associated with the work entry types.
       * The assumption that a work entry, even minimal (at least 1 hour) is enough to grant the benefit for
         that day.
    """
    _name = 'l10n_be.work.entry.daily.benefit.report'
    _description = 'Work Entry Related Benefit Report'
    _auto = False

    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    day = fields.Date(readonly=True)
    benefit_name = fields.Char('Benefit Name', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        work_entry_type_benefits = self.env['hr.work.entry.type'].get_work_entry_type_benefits()
        statement = sql.SQL("""
            CREATE OR REPLACE VIEW {table_name} AS (
                WITH hr_work_entry_type_providing_advantages AS (
                    SELECT id,
                           {field_list}
                    FROM   hr_work_entry_type
                    WHERE  meal_voucher = true OR
                           private_car = true OR
                           representation_fees = true
                ),
                hr_work_entry_split_in_days AS (
                    SELECT     employee_id,
                               GREATEST (day_serie, date_start) AS date_start_day,
                               LEAST(day_serie + INTERVAL '1 day', date_stop) AS date_stop_day,
                               {field_list}
                    FROM       hr_work_entry AS work_entry
                    INNER JOIN hr_work_entry_type_providing_advantages AS work_entry_type ON work_entry.work_entry_type_id = work_entry_type.id
                    CROSS JOIN generate_series(date_trunc('day', work_entry.date_start), date_trunc('day', work_entry.date_stop), INTERVAL '1 day') AS day_serie
                    WHERE      work_entry.state IN ('draft', 'validated')
                ),
                hr_work_entry_one_advantage_per_row AS (
                    SELECT     employee_id,
                               date_start_day,
                               date_stop_day,
                               advantage.benefit_name,
                               advantage.is_applicable
                    FROM       hr_work_entry_split_in_days
                    CROSS JOIN LATERAL (VALUES {lateral_values_field_list}) AS advantage(benefit_name, is_applicable)
                )
                SELECT   ROW_NUMBER() OVER(ORDER BY employee_id, date_start_day::date, benefit_name) AS id,
                         employee_id,
                         date_start_day::date AS day,
                         benefit_name
                FROM     hr_work_entry_one_advantage_per_row
                WHERE    is_applicable = true
                GROUP BY employee_id, benefit_name, date_start_day::date, date_stop_day::date
                HAVING SUM(date_part('hour', date_stop_day - date_start_day)) > 0
            );
        """).format(
            table_name=sql.Identifier(self._table),
            field_list=sql.SQL(',').join(
                        [sql.Identifier(work_entry_type_benefit) for work_entry_type_benefit in work_entry_type_benefits]),
            lateral_values_field_list=sql.SQL(',').join(
                        [sql.SQL("({benefit_name}, {benefit_value})").format(benefit_name=sql.Literal(work_entry_type_benefit), benefit_value=sql.Identifier(work_entry_type_benefit)) for work_entry_type_benefit in work_entry_type_benefits]))
        self._cr.execute(statement)
