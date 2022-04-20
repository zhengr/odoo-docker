# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib

from collections import defaultdict
from odoo import fields, http, models, SUPERUSER_ID, _

from odoo.addons.sign.controllers.main import Sign
from odoo.http import request
from odoo.tools import consteq
from odoo.tools.image import image_data_uri
from werkzeug.exceptions import NotFound
from werkzeug.wsgi import get_current_url


class SignContract(Sign):

    @http.route([
        '/sign/sign/<int:id>/<token>',
        '/sign/sign/<int:id>/<token>/<sms_token>'
        ], type='json', auth='public')
    def sign(self, id, token, sms_token=False, signature=None):
        result = super(SignContract, self).sign(id, token, sms_token=sms_token, signature=signature)
        request_item = request.env['sign.request.item'].sudo().search([('access_token', '=', token)])
        contract = request.env['hr.contract'].sudo().with_context(active_test=False).search([
            ('sign_request_ids', 'in', request_item.sign_request_id.ids)])
        request_template_id = request_item.sign_request_id.template_id.id
        # Only if the signed document is the document to sign from the salary package
        contract_documents = [
            contract.sign_template_id.id,
            contract.contract_update_template_id.id,
        ]
        if contract and request_template_id in contract_documents:
            self._update_contract_on_signature(request_item, contract)
            return {'url': '/salary_package/thank_you/' + str(contract.id)}
        return result

    def _update_contract_on_signature(self, request_item, contract):
        # Only the applicant/employee has signed
        if request_item.sign_request_id.nb_closed == 1:
            contract.active = True
            contract.hash_token = False
            if contract.applicant_id:
                contract.applicant_id.access_token = False
                contract.applicant_id.emp_id = contract.employee_id
        # Both applicant/employee and HR responsible have signed
        if request_item.sign_request_id.nb_closed == 2:
            if contract.employee_id:
                contract.employee_id.active = True
            if contract.employee_id.address_home_id:
                contract.employee_id.address_home_id.active = True


class HrContractSalary(http.Controller):

    def _check_access_rights(self, contract_id):
        contract_sudo = request.env['hr.contract'].sudo().browse(contract_id)
        if not contract_sudo.employee_id or contract_sudo.employee_id.user_id == request.env.user:
            return contract_sudo
        try:
            contract = request.env['hr.contract'].with_context(allowed_company_ids=request.env.user.company_ids.ids).browse(contract_id)
            contract.check_access_rights('read')
            contract.check_access_rule('read')
            return contract_sudo
        except:
            return request.env['hr.contract']

    @http.route(['/salary_package/simulation/contract/<int:contract_id>'], type='http', auth="public", website=True)
    def salary_package(self, contract_id=None, **kw):

        # Used to flatten the response after the rollback.
        # Otherwise assets are generated and rollbacked before the page loading.
        # Leading to crashes (assets not found) when loading the page.
        response = False
        request.env.cr.execute('SAVEPOINT salary')

        contract = request.env['hr.contract'].sudo().browse(contract_id)
        if not contract.exists():
            return request.render('http_routing.http_error', {'status_code': 'Oops',
                                                         'status_message': 'This contract has been updated, please request an updated link..'})

        if not request.env.user.has_group('hr_contract.group_hr_contract_manager'):
            if kw.get('applicant_id'):
                applicant = request.env['hr.applicant'].sudo().browse(int(kw.get('applicant_id')))
                if not kw.get('token') or \
                        not applicant.access_token or \
                        not consteq(applicant.access_token, kw.get('token')) or \
                        applicant.access_token_end_date < fields.Date.today():
                    return request.render(
                        'http_routing.http_error',
                        {'status_code': 'Oops',
                         'status_message': 'This link is invalid. Please contact the HR Responsible to get a new one...'})
            if contract.employee_id and not contract.employee_id.user_id and not kw.get('applicant_id'):
                return request.render(
                    'http_routing.http_error',
                    {'status_code': 'Oops',
                     'status_message': 'The employee is not linked to an existing user, please contact the administrator..'})
            if contract.employee_id and contract.employee_id.user_id != request.env.user:
                raise NotFound()

        if kw.get('employee_contract_id'):
            employee_contract = request.env['hr.contract'].sudo().browse(int(kw.get('employee_contract_id')))
            if not request.env.user.has_group('hr_contract.group_hr_contract_manager') and employee_contract.employee_id \
                    and employee_contract.employee_id.user_id != request.env.user:
                raise NotFound()

        if not contract.employee_id:
            be_country = request.env["res.country"].search([("code", "=", "BE")])
            contract.employee_id = request.env['hr.employee'].sudo().create({
                'name': '',
                'active': False,
                'country_id': be_country.id,
            })
            contract.employee_id.address_home_id = request.env['res.partner'].sudo().create({
                'name': 'Simulation',
                'type': 'private',
                'country_id': be_country.id,
                'active': False,
            })

        values = self._get_salary_package_values(contract)

        redirect_to_job = False
        applicant_id = False
        contract_type = False
        employee_contract_id = False
        job_title = False

        final_yearly_costs = contract.final_yearly_costs

        for field_name, value in kw.items():
            old_value = contract
            if field_name == 'job_id':
                redirect_to_job = value
            elif field_name == 'applicant_id':
                applicant_id = value
            elif field_name == 'employee_contract_id':
                employee_contract_id = value
            elif field_name == 'contract_type':
                contract_type = value
            elif field_name == 'job_title':
                job_title = value
            elif field_name in old_value:
                old_value = old_value[field_name]
            else:
                old_value = ""

            if isinstance(old_value, models.BaseModel):
                old_value = ""
            elif old_value:
                try:
                    value = float(value)
                except:
                    continue
                if field_name == "final_yearly_costs":
                    final_yearly_costs = value
                else:
                    setattr(contract, field_name, value)

        new_gross = contract.sudo()._get_gross_from_employer_costs(final_yearly_costs)
        contract.wage = new_gross

        values.update({
            'need_personal_information': not redirect_to_job,
            'submit': not redirect_to_job,
            'redirect_to_job': redirect_to_job,
            'applicant_id': applicant_id,
            'employee_contract_id': employee_contract_id,
            'contract_type': contract_type,
            'job_title': job_title,
            'default_mobile': request.env['ir.default'].sudo().get('hr.contract', 'mobile'),
            'original_link': get_current_url(request.httprequest.environ),
            'token': kw.get('token')})

        response = request.render("hr_contract_salary.salary_package", values)
        response.flatten()
        request.env['hr.contract'].sudo().flush()
        request.env.cr.precommit.clear()
        request.env.cr.execute('ROLLBACK TO SAVEPOINT salary')
        return response

    @http.route(['/salary_package/thank_you/<int:contract_id>'], type='http', auth="public", website=True)
    def salary_package_thank_you(self, contract_id=None, **kw):
        contract = request.env['hr.contract'].sudo().browse(contract_id)
        return request.render("hr_contract_salary.salary_package_thank_you", {
            'responsible_name': contract.hr_responsible_id.partner_id.name or contract.job_id.user_id.partner_id.name,
            'responsible_email': contract.hr_responsible_id.partner_id.email or contract.job_id.user_id.partner_id.email,
            'responsible_phone': contract.hr_responsible_id.partner_id.phone or contract.job_id.user_id.partner_id.phone,
        })

    def _get_personal_infos(self, contract):
        initial_values = {}
        dropdown_options = {}
        targets = {
            'employee': contract.employee_id,
            'address': contract.employee_id.address_home_id,
            'bank_account': contract.employee_id.bank_account_id,
        }

        countries = request.env['res.country'].search([])
        states = request.env['res.country.state'].search([])
        langs = request.env['res.lang'].search([])

        # PERSONAL INFOS
        personal_infos = request.env['hr.contract.salary.personal.info'].sudo().search([
            '|',
            ('structure_type_id', '=', False),
            ('structure_type_id', '=', contract.structure_type_id.id)])
        mapped_personal_infos = [
            defaultdict(lambda: request.env['hr.contract.salary.personal.info']), # Main Panel
            request.env['hr.contract.salary.personal.info'], # Side Panel
        ]
        for personal_info in personal_infos:
            if personal_info.position == 'left':
                mapped_personal_infos[0][personal_info.info_type_id.name] |= personal_info
            else:
                mapped_personal_infos[1] |= personal_info

            target = targets[personal_info.applies_on]

            if personal_info.display_type == 'document':
                if personal_info.field in target and target[personal_info.field]:
                    if target[personal_info.field][:7] == b'JVBERi0':
                        content = "data:application/pdf;base64,%s" % (target[personal_info.field].decode())
                    else:
                        content = image_data_uri(target[personal_info.field])
                else:
                    content = False
                initial_values[personal_info.field] = content
            else:
                initial_values[personal_info.field] = target[personal_info.field] if personal_info.field in target else ''

            if personal_info.display_type == 'dropdown':
                # Set record id instead of browse record as value
                if isinstance(initial_values[personal_info.field], models.BaseModel):
                    initial_values[personal_info.field] = initial_values[personal_info.field].id

                if personal_info.dropdown_selection == 'specific':
                    values = [(value.value, value.name) for value in personal_info.value_ids]
                elif personal_info.dropdown_selection == 'country':
                    values = [(country.id, country.name) for country in countries]
                elif personal_info.dropdown_selection == 'state':
                    values = [(state.id, state.name) for state in states]
                elif personal_info.dropdown_selection == 'lang':
                    values = [(lang.id, lang.name) for lang in langs]
                dropdown_options[personal_info.field] = values
        return mapped_personal_infos, dropdown_options, initial_values

    def _get_advantages(self, contract):
        return request.env['hr.contract.salary.advantage'].sudo().search([
            ('structure_type_id', '=', contract.structure_type_id.id)])

    def _get_advantages_values(self, contract):
        initial_values = {}
        dropdown_options = {}

        # ADVANTAGES
        advantages = self._get_advantages(contract)
        mapped_advantages = defaultdict(lambda: request.env['hr.contract.salary.advantage'])
        for advantage in advantages:
            mapped_advantages[advantage.advantage_type_id] |= advantage
            field = advantage.field
            initial_values[field] = contract[field]

            if advantage.folded:
                fold_field = 'fold_%s' % (advantage.field)
                advantage_fold_field = advantage.fold_field or advantage.field
                initial_values[fold_field] = contract[advantage_fold_field] if advantage_fold_field and advantage_fold_field in contract else 0

            if advantage.display_type == 'manual':
                manual_field = '%s_manual' % (advantage.field)
                field = advantage.manual_field or advantage.field
                initial_values[manual_field] = contract[field] if field and field in contract else 0
            elif advantage.display_type == 'dropdown':
                initial_values['select_%s' % field] = contract[field]

        dropdown_advantages = advantages.filtered(lambda a: a.display_type == 'dropdown')
        for dropdown_advantage in dropdown_advantages:
            dropdown_options[dropdown_advantage.field] = [(value.value, value.value) for value in dropdown_advantage.value_ids]
        advantage_types = sorted(advantages.mapped('advantage_type_id'), key=lambda x: x.sequence)
        return mapped_advantages, advantage_types, dropdown_options, initial_values

    def _get_salary_package_values(self, contract):
        mapped_personal_infos, dropdown_options_1, initial_values_1 = self._get_personal_infos(contract)
        mapped_advantages, advantage_types, dropdown_options_2, initial_values_2 = self._get_advantages_values(contract)
        all_initial_values = {**initial_values_1, **initial_values_2}
        all_initial_values = {key: round(value, 2) if isinstance(value, float) else value for key, value in all_initial_values.items()}
        all_dropdown_options = {**dropdown_options_1, **dropdown_options_2}

        return {
            'contract': contract,
            'states': request.env['res.country.state'].search([]),
            'countries': request.env['res.country'].search([]),
            'advantages': mapped_advantages,
            'advantage_types': advantage_types,
            'mapped_personal_infos': mapped_personal_infos,
            'dropdown_options': all_dropdown_options,
            'initial_values': all_initial_values,
        }

    def _get_new_contract_values(self, contract, employee, advantages):
        contract_advantages = self._get_advantages(contract)
        contract_vals = {
            'active': False,
            'name': contract.name if contract.state == 'draft' else "Package Simulation",
            'job_id': contract.job_id.id,
            'company_id': contract.company_id.id,
            'currency_id': contract.company_id.currency_id.id,
            'employee_id': employee.id,
            'structure_type_id': contract.structure_type_id.id,
            'wage': advantages['wage'],
            'resource_calendar_id': contract.resource_calendar_id.id,
            'default_contract_id': contract.default_contract_id.id,
            'hr_responsible_id': contract.hr_responsible_id.id,
            'sign_template_id': contract.sign_template_id.id,
            'contract_update_template_id': contract.contract_update_template_id.id,
            'date_start': fields.Date.today().replace(day=1),
            'contract_type': contract.contract_type,
        }
        for advantage in contract_advantages:
            if advantage.field not in contract:
                continue
            if hasattr(contract, '_get_advantage_values_%s' % (advantage.field)):
                contract_vals.update(getattr(contract, '_get_advantage_values_%s' % (advantage.field))(contract, advantages))
                continue
            if advantage.folded:
                contract_vals[advantage.fold_field or advantage.field] = advantages['fold_%s' % (advantage.field)]
            if advantage.display_type == 'dropdown':
                contract_vals[advantage.field] = advantages[advantage.field]
            if advantage.display_type == 'manual':
                contract_vals[advantage.manual_field or advantage.field] = advantages['%s_manual' % (advantage.field)]
            else:
                contract_vals[advantage.field] = advantages[advantage.field]
        return contract_vals

    def _update_personal_info(self, employee, contract, personal_infos_values, no_name_write=False):
        def resolve_value(field_name, values):
            targets = {
                'employee': request.env['hr.employee'],
                'address': request.env['res.partner'],
                'bank_account': request.env['res.partner.bank'],
            }
            field_value = values[field_name]

            target = targets[personal_info.applies_on]
            if field_name in target and isinstance(target[field_name], models.BaseModel):
                field_value = int(field_value) if field_value else False
            return field_value

        personal_infos = request.env['hr.contract.salary.personal.info'].sudo().search([
            '|', ('structure_type_id', '=', False), ('structure_type_id', '=', contract.structure_type_id.id)])

        employee_infos = personal_infos_values['employee']
        address_infos = personal_infos_values['address']
        bank_account_infos = personal_infos_values['bank_account']
        employee_vals = {'job_title': employee_infos['job_title']}
        address_home_vals = {}
        bank_account_vals = {}
        for personal_info in personal_infos:
            field_name = personal_info.field

            if personal_info.display_type == 'document' and not employee_infos.get(field_name):
                continue

            if field_name in employee_infos and personal_info.applies_on == 'employee':
                employee_vals[field_name] = resolve_value(field_name, employee_infos)
            elif field_name in address_infos and personal_info.applies_on == 'address':
                address_home_vals[field_name] = resolve_value(field_name, address_infos)
            elif field_name in bank_account_infos and personal_info.applies_on == 'bank_account':
                bank_account_vals[field_name] = resolve_value(field_name, bank_account_infos)

        address_home_vals['name'] = employee_vals['name']

        # Update personal info on the private address
        if employee.address_home_id:
            if no_name_write:
                del address_home_vals['name']
            partner = employee.address_home_id
            # We shouldn't modify the partner email like this
            address_home_vals.pop('email', None)
            partner.write(address_home_vals)
        else:
            address_home_vals['active'] = False
            partner = request.env['res.partner'].sudo().with_context(lang=None).create(address_home_vals)

        # Update personal info on the employee
        bank_account_vals['partner_id'] = partner.id
        existing_bank_account = request.env['res.partner.bank'].sudo().search([
            ('acc_number', '=', bank_account_vals['acc_number'])], limit=1)
        if existing_bank_account:
            bank_account = existing_bank_account
        else:
            bank_account = request.env['res.partner.bank'].sudo().create(bank_account_vals)

        employee_vals['bank_account_id'] = bank_account.id
        employee_vals['address_home_id'] = partner.id

        if partner.type != 'private':
            partner.type = 'private'

        if not no_name_write:
            employee_vals['name'] = employee_infos['name']
        employee.write(employee_vals)

    def create_new_contract(self, contract, advantages, no_write=False, **kw):
        # Generate a new contract with the current modifications
        contract_values = advantages['contract']
        personal_infos = {
            'employee': advantages['employee'],
            'address': advantages['address'],
            'bank_account': advantages['bank_account'],
        }
        applicant = request.env['hr.applicant'].sudo().browse(kw.get('applicant_id')).exists()
        employee = kw.get('employee') or contract.employee_id or applicant.emp_id
        if not employee and applicant:
            existing_contract = request.env['hr.contract'].sudo().with_context(active_test=False).search([
                ('applicant_id', '=', applicant.id), ('employee_id', '!=', False)], limit=1)
            employee = existing_contract.employee_id
        if not employee:
            employee = request.env['hr.employee'].sudo().create({
                'name': 'Simulation Employee',
                'active': False,
                'company_id': contract.company_id.id,
            })
        self._update_personal_info(employee, contract, personal_infos, no_name_write=bool(kw.get('employee')))
        new_contract = request.env['hr.contract'].sudo().new(self._get_new_contract_values(contract, employee, contract_values))

        new_contract.wage_with_holidays = contract_values['wage']
        new_contract.final_yearly_costs = float(contract_values['final_yearly_costs'] or 0.0)
        new_contract._inverse_wage_with_holidays()

        vals = new_contract._convert_to_write(new_contract._cache)

        if not no_write and contract.state == 'draft':
            contract.write(vals)
        else:
            contract = request.env['hr.contract'].sudo().create(vals)

        return contract

    @http.route('/salary_package/update_salary', type="json", auth="public")
    def update_salary(self, contract_id=None, advantages=None, **kw):
        result = {}
        contract = self._check_access_rights(contract_id)

        new_contract = self.create_new_contract(contract, advantages)
        new_gross = new_contract._get_gross_from_employer_costs(float(advantages['contract']['final_yearly_costs'] or 0.0))
        new_contract.wage = new_gross

        result['new_gross'] = round(new_gross, 2)
        result.update(self._get_compute_results(new_contract))

        request.env.cr.rollback()
        return result

    def _get_compute_results(self, new_contract):
        result = {}
        result['wage_with_holidays'] = round(new_contract.wage_with_holidays, 2)
        resume_lines = request.env['hr.contract.salary.resume'].search([
            '|',
            ('structure_type_id', '=', False),
            ('structure_type_id', '=', new_contract.structure_type_id.id),
            ('value_type', 'in', ['fixed', 'contract', 'monthly_total', 'sum'])])

        result['resume_categories'] = [c.name for c in sorted(resume_lines.mapped('category_id'), key=lambda x: x.sequence)]
        result['resume_lines_mapped'] = defaultdict(lambda: {})

        monthly_total = 0
        monthly_total_lines = resume_lines.filtered(lambda l: l.value_type == 'monthly_total')

        uoms = {'days': _('Days'), 'percent': '%', 'currency': new_contract.company_id.currency_id.symbol}

        for resume_line in resume_lines - monthly_total_lines:
            value = 0
            uom = uoms[resume_line.uom]
            if resume_line.value_type == 'fixed':
                value = resume_line.fixed_value
            if resume_line.value_type == 'contract':
                value = new_contract[resume_line.code] if resume_line.code in new_contract else 0
            if resume_line.value_type == 'sum':
                for advantage in resume_line.advantage_ids:
                    if not advantage.fold_field or (advantage.fold_field and new_contract[advantage.fold_field]):
                        field = advantage.field
                        value += new_contract[field]
            if resume_line.impacts_monthly_total:
                monthly_total += value / 12.0 if resume_line.category_id.periodicity == 'yearly' else value
            try:
                value = round(float(value), 2)
            except:
                pass
            result['resume_lines_mapped'][resume_line.category_id.name][resume_line.code] = (resume_line.name, value, uom)
        for resume_line in monthly_total_lines:
            result['resume_lines_mapped'][resume_line.category_id.name][resume_line.code] = (resume_line.name, round(float(monthly_total), 2), uoms['currency'])
        return result

    @http.route(['/salary_package/onchange_advantage/'], type='json', auth='public')
    def onchange_advantage(self, advantage_field, new_value, contract_id, advantages):
        # Return a dictionary describing the new advantage configuration:
        # - new_value: The advantage new_value (same by default)
        # - description: The dynamic description corresponding to the advantage new value
        # - extra_value: A list of tuple (input name, input value) change another input due
        #                to the advantage new_value
        # Override this controllers to add customize
        # the returned value for a specific advantage
        contract = self._check_access_rights(contract_id)
        advantage = request.env['hr.contract.salary.advantage'].sudo().search([
            ('structure_type_id', '=', contract.structure_type_id.id),
            ('res_field_id.name', '=', advantage_field)])
        if hasattr(contract, '_get_description_%s' % advantage_field):
            description = getattr(contract, '_get_description_%s' % advantage_field)(new_value)
        else:
            description = advantage.description
        return {'new_value': new_value, 'description': description, 'extra_values': False}

    @http.route(['/salary_package/onchange_personal_info/'], type='json', auth='public')
    def onchange_personal_info(self, field, value):
        # sudo as public users can't access ir.model.fields
        info = request.env['hr.contract.salary.personal.info'].sudo().search([('field', '=', field)])
        if not info.child_ids:
            return {}
        if info.value_ids:
            value = info.value_ids.filtered(lambda v: v.value == value)
            return {'hide_children': value.hide_children, 'field': field}
        return {'hide_children': not bool(value), 'field': field}

    def _get_email_info(self, contract, **kw):
        field_names = {
            model: {
                field.name: field.field_description for field in request.env['ir.model.fields'].sudo().search([('model', '=', model)])
            } for model in ['hr.employee', 'hr.contract', 'res.partner', 'res.partner.bank']}
        result = {
            _('Salary Package Summary'): {
                'General Information': [
                    (_('Employee Name'), contract.employee_id.name),
                    (_('Job Position'), contract.job_id.name),
                    (_('Job Title'), contract.employee_id.job_title),
                    (_('Contract Type'), kw.get('contract_type')),
                    (_('Original Link'), kw.get('original_link'))
                ],
            }
        }
        # Contract Information
        contract_advantages = request.env['hr.contract.salary.advantage'].sudo().search([('structure_type_id', '=', contract.structure_type_id.id)])
        contract_info = {advantage_type.name: [] for advantage_type in sorted(contract_advantages.mapped('advantage_type_id'), key=lambda x: x.sequence)}
        for advantage in contract_advantages:
            if advantage.folded and advantage.fold_field:
                value = _('Yes') if contract[advantage.fold_field] else _('No')
                contract_info[advantage.advantage_type_id.name].append((field_names['hr.contract'][advantage.fold_field], value))
            field_name = advantage.field
            if field_name not in contract:
                continue
            field_value = contract[field_name]
            if isinstance(field_value, models.BaseModel):
                field_value = field_value.name
            elif isinstance(field_value, float):
                field_value = round(field_value, 2)
            contract_info[advantage.advantage_type_id.name].append((field_names['hr.contract'][field_name], field_value))
        # Add wage information
        contract_info[_('Wage')] = [
            (_('Monthly Gross Salary'), contract.wage_with_holidays),
            (_('Annual Employer Cost'), contract.final_yearly_costs),
        ]
        result[_('Contract Information:')] = contract_info
        # Personal Information
        infos = request.env['hr.contract.salary.personal.info'].sudo().search([('display_type', '!=', 'document'), '|', ('structure_type_id', '=', False), ('structure_type_id', '=', contract.structure_type_id.id)])
        personal_infos = {personal_info_type.name: [] for personal_info_type in sorted(infos.mapped('info_type_id'), key=lambda x: x.sequence)}
        for info in infos:
            if info.applies_on == 'employee':
                field_label = field_names['hr.employee'][info.field]
                field_value = contract.employee_id[info.field]
            if info.applies_on == 'address':
                field_label = field_names['res.partner'][info.field]
                field_value = contract.employee_id.address_home_id[info.field]
            if info.applies_on == 'bank_account':
                field_label = field_names['res.partner.bank'][info.field]
                field_value = contract.employee_id.bank_account_id[info.field]
            if isinstance(field_value, models.BaseModel):
                field_value = field_value.name
            elif isinstance(field_value, float):
                field_value = round(field_value, 2)
            personal_infos[info.info_type_id.name].append((field_label, field_value))
        result[_('Personal Information')] = personal_infos
        return {'mapped_data': result}

    def send_email(self, contract, **kw):
        values = self._get_email_info(contract, **kw)
        model = 'hr.applicant' if kw.get('applicant_id') else 'hr.contract'
        res_id = kw.get('applicant_id') or kw.get('employee_contract_id')
        request.env[model].sudo().browse(res_id).message_post_with_view(
            'hr_contract_salary.hr_contract_salary_email_template',
            values=values)
        return contract.id

    @http.route(['/salary_package/submit/'], type='json', auth='public')
    def submit(self, contract_id=None, advantages=None, **kw):
        contract = self._check_access_rights(contract_id)
        if kw.get('employee_contract_id', False):
            contract = request.env['hr.contract'].sudo().browse(kw.get('employee_contract_id'))
            if contract.employee_id.user_id == request.env.user:
                kw['employee'] = contract.employee_id
        kw['package_submit'] = True
        new_contract = self.create_new_contract(contract, advantages, no_write=True, **kw)
        self.send_email(new_contract, **kw)

        applicant = request.env['hr.applicant'].sudo().browse(kw.get('applicant_id')).exists()
        if applicant and kw.get('token', False):
            hash_token_access = hashlib.sha1(kw.get('token').encode("utf-8")).hexdigest()
            existing_contract = request.env['hr.contract'].sudo().search([
                ('applicant_id', '=', applicant.id), ('hash_token', '=', hash_token_access), ('active', '=', False)])
            existing_contract.sign_request_ids.write({'state': 'canceled', 'active': False})
            existing_contract.unlink()
            new_contract.hash_token = hash_token_access
        elif not applicant and contract.employee_id.user_id and contract.employee_id.user_id == request.env.user and kw.get('original_link', False):
            hash_token_access = hashlib.sha1(kw.get('original_link').encode("utf-8")).hexdigest()
            existing_contract = request.env['hr.contract'].sudo().search([
                ('employee_id', 'in', request.env.user.employee_ids.ids), ('hash_token', '=', hash_token_access), ('active', '=', False)])
            existing_contract.sign_request_ids.write({'state': 'canceled', 'active': False})
            existing_contract.unlink()
            new_contract.hash_token = hash_token_access

        if new_contract.id != contract.id:
            new_contract.write({
                'state': 'draft',
                'name': 'New contract - ' + new_contract.employee_id.name,
                'origin_contract_id': contract_id,
            })
        sign_template = new_contract.contract_update_template_id if kw.get('employee_contract_id') else new_contract.sign_template_id
        if not sign_template:
            return {'error': 1, 'error_msg': _('No signature template defined on the contract. Please contact the HR responsible.')}
        if not new_contract.hr_responsible_id:
            return {'error': 1, 'error_msg': _('No HR responsible defined on the job position. Please contact an administrator.')}

        if not request.env.user.email_formatted:
            sign_request = request.env['sign.request'].with_user(SUPERUSER_ID)
        else:
            sign_request = request.env['sign.request'].sudo()

        res = sign_request.initialize_new(
            sign_template.id,
            [
                {'role': request.env.ref('sign.sign_item_role_employee').id, 'partner_id': new_contract.employee_id.address_home_id.id},
                {'role': request.env.ref('hr_contract_sign.sign_item_role_job_responsible').id, 'partner_id': new_contract.hr_responsible_id.partner_id.id}
            ],
            [new_contract.hr_responsible_id.partner_id.id],
            'Signature Request - ' + new_contract.name,
            'Signature Request - ' + new_contract.name,
            '',
            False
        )

        # Prefill the sign boxes
        items = request.env['sign.item'].sudo().search([
            ('template_id', '=', sign_template.id),
            ('name', '!=', '')
        ])
        for item in items:
            new_value = new_contract
            for elem in item.name.split('.'):
                if elem in new_value:
                    new_value = new_value[elem]
                else:
                    new_value = ''
                if elem == 'car' and new_contract.transport_mode_car:
                    if not new_contract.new_car and new_contract.car_id:
                        new_value = new_contract.car_id.model_id.name
                    elif new_contract.new_car and new_contract.new_car_model_id:
                        new_value = new_contract.new_car_model_id.name
            if isinstance(new_value, models.BaseModel):
                new_value = ''
            if isinstance(new_value, float):
                new_value = round(new_value, 2)
            if new_value or (new_value == 0.0):
                sign_request_item_id = http.request.env['sign.request.item'].sudo().search([
                    ('sign_request_id', '=', res['id']),
                    ('role_id', '=', item.responsible_id.id)
                ])
                request.env['sign.request.item.value'].sudo().create({
                    'sign_item_id': item.id,
                    'sign_request_id': res['id'],
                    'value': new_value,
                    'sign_request_item_id': sign_request_item_id.id
                })

        sign_request = request.env['sign.request'].browse(res['id']).sudo()
        sign_request.toggle_favorited()
        sign_request.action_sent()
        sign_request.write({'state': 'sent'})
        sign_request.request_item_ids.write({'state': 'sent'})

        access_token = request.env['sign.request.item'].sudo().search([
            ('sign_request_id', '=', res['id']),
            ('role_id', '=', request.env.ref('sign.sign_item_role_employee').id)
        ]).access_token

        new_contract.sign_request_ids += sign_request

        if new_contract:
            if kw.get('applicant_id'):
                new_contract.sudo().applicant_id = kw.get('applicant_id')
            if kw.get('employee_contract_id'):
                new_contract.sudo().origin_contract_id = kw.get('employee_contract_id')

        return {'job_id': new_contract.job_id.id, 'request_id': res['id'], 'token': access_token, 'error': 0, 'new_contract_id': new_contract.id}
