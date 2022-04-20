# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.survey.controllers.main import Survey
from odoo import http
from odoo.http import request
from odoo.osv import expression


class AppraisalSurvey(Survey):

    def _get_user_input_domain(self, survey, line_filter_domain, **post):
        user_input_domain = super()._get_user_input_domain(survey, line_filter_domain, **post)
        if not post.get('appraisal_id'):
            return user_input_domain
        appraisal = request.env['hr.appraisal'].browse(int(post.get('appraisal_id')))
        user = request.env.user
        if user in appraisal.manager_ids.mapped('user_id'):
            return expression.AND([[('appraisal_id', '=', appraisal.id)], user_input_domain])
        if user in appraisal.employee_feedback_ids.mapped('user_id'):
            return expression.AND([[
                ('appraisal_id', '=', appraisal.id),
                ('partner_id', '=', user.partner_id.id)
            ], user_input_domain])

    @http.route('/appraisal/<int:appraisal_id>/results', type='http', auth='user', website=True)
    def appraisal_survey_results(self, appraisal_id, **post):
        """ Display survey Results & Statistics for given appraisal.
        """
        # check access rigths using token, get back survey if granted
        appraisal = request.env['hr.appraisal'].browse(int(appraisal_id))
        if appraisal.employee_id.user_id == request.env.user:
            return request.render(
                'http_routing.http_error',
                {'status_code': 'Oops',
                 'status_message': "Sorry, you can't access to this survey concerning your appraisal..."})
        user = request.env.user
        if user.has_group('hr_appraisal.group_hr_appraisal_manager') or user.has_group('base.group_system') \
                or user in appraisal.manager_ids.mapped('user_id'):
            survey_sudo = request.env['survey.user_input'].sudo().search([('appraisal_id', '=', appraisal.id)], limit=1).survey_id
        if user in appraisal.employee_feedback_ids.mapped('user_id'):
            answer = request.env['survey.user_input'].sudo().search([
                ('appraisal_id', '=', appraisal.id),
                ('partner_id', '=', request.env.user.partner_id.id),
            ], limit=1)
            if answer:
                survey_sudo = answer.survey_id

        user_input_lines_sudo, search_filters = self._extract_filters_data(survey_sudo, post)
        survey_data = survey_sudo._prepare_statistics(user_input_lines_sudo)
        question_and_page_data = survey_sudo.question_and_page_ids._prepare_statistics(user_input_lines_sudo)

        template_values = {
            'survey': survey_sudo,
            'question_and_page_data': question_and_page_data,
            'survey_data': survey_data,
            'search_filters': search_filters,
            'search_finished': 'true',  # always finished
            'appraisal_id': appraisal_id,
        }
        return request.render('survey.survey_page_statistics', template_values)
