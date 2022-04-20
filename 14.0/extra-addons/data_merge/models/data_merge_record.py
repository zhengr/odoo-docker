# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, tools
from odoo.exceptions import ValidationError
from odoo.models import MAGIC_COLUMNS
from odoo.osv.expression import OR
from odoo.tools.misc import format_datetime, format_date

from datetime import datetime, date
import psycopg2
import ast
import logging
_logger = logging.getLogger(__name__)


class DataMergeRecord(models.Model):
    _name = 'data_merge.record'
    _description = 'Deduplication Record'
    _order = 'res_id desc'

    active = fields.Boolean(compute='_compute_active', store=True)
    group_id = fields.Many2one('data_merge.group', string='Record Group', ondelete='cascade', required=True, index=True)
    model_id = fields.Many2one(related='group_id.model_id', store=True, readonly=True, index=True)
    res_model_id = fields.Many2one(related='group_id.res_model_id', store=True, readonly=True)
    res_model_name = fields.Char(related='group_id.res_model_name', store=True, readonly=True)
    is_master = fields.Boolean(default=False)
    is_deleted = fields.Boolean(compute='_compute_fields')
    is_discarded = fields.Boolean(default=False)

    # Original Record
    name = fields.Char(compute='_compute_fields')
    res_id = fields.Integer(string='Record ID', readonly=False, group_operator=None, index=True)
    record_create_date = fields.Datetime(string='Created On', compute='_compute_fields')
    record_create_uid = fields.Char(string='Created By', compute='_compute_fields')
    record_write_date = fields.Datetime(string='Updated On', compute='_compute_fields')
    record_write_uid = fields.Char(string='Updated By', compute='_compute_fields')

    differences = fields.Char(string='Differences',
        help='Differences with the master record', compute='_compute_differences', store=True)
    field_values = fields.Char(string='Field Values',
        compute='_compute_field_values')
    used_in = fields.Char(string='Used In',
        help='List of other models referencing this record', compute='_compute_usage', store=True)


    #############
    ### Computes
    #############
    def _render_values(self, to_read):
        self.ensure_one()

        def format_value(value, env):
            if isinstance(value, tuple):
                return value[1]
            if isinstance(value, datetime):
                return format_datetime(env, value, dt_format='short')
            if isinstance(value, date):
                return format_date(env, value)
            return value

        IrField = lambda key: self.env['ir.model.fields']._get(self.res_model_name, key)
        field_description = lambda key: IrField(key)['field_description']

        # Hide fields with an attr 'groups' defined or from the blacklisted fields
        hidden_field = lambda key: key in MAGIC_COLUMNS or \
            self.env[self.res_model_name]._fields[key].groups or \
            IrField(key)['ttype'] == 'binary'

        record = self._original_records()
        if not record:
            return dict()

        record_data = record.read(to_read)[0]
        return {str(field_description(key)):str(format_value(value, self.env)) for key, value in record_data.items() if value and not hidden_field(key)}


    @api.depends('res_id')
    def _compute_field_values(self):
        model_fields = {}
        for record in self:
            if record.model_id not in model_fields.keys():
                model_fields[record.model_id] = record.model_id.rule_ids.mapped('field_id.name')
            to_read = model_fields[record.model_id]

            if not to_read:
                record.field_values = ''
            else:
                record.field_values = ', '.join([v for k,v in record._render_values(to_read).items()])

    @api.depends('res_id')
    def _compute_differences(self):
        model_list_fields = {}
        for model in list(set(self.mapped('res_model_name'))):
            view = self.env[model].load_views([(False, 'list')])
            list_fields = view['fields_views']['list']['fields'].keys()
            model_list_fields[model] = list_fields

        for record in self:
            list_fields = model_list_fields[record.res_model_name]
            read_fields = record.group_id.divergent_fields.split(',') & list_fields
            if read_fields != {''}:
                record.differences = ', '.join(['%s: %s' % (k, v) for k,v in record._render_values(read_fields).items()])
            else:
                record.differences = ''

    def _get_references(self):
        """
        Count all the references for the records.

        :return dict of tuples with the record ID as key
            (count, model, model name, fields)
                - `count`: number of records
                - `model`: technical model name (res.partner)
                - `model name`: "human" name (Contact)
                - `fields`: list of fields from the model referencing the record
        """
        res_models = list(set(self.mapped('res_model_name')))
        # Get the relevant fields for each model
        model_fields = dict.fromkeys(res_models, self.env['ir.model.fields'])
        all_fields = self.env['ir.model.fields'].sudo().search([
            ('store', '=', True),
            ('ttype', 'in', ('one2many', 'many2one', 'many2many')),
            ('relation', 'in', res_models),
            ('index', '=', True),
        ])
        for field in all_fields:
            if not isinstance(self.env[field.model], models.BaseModel) or \
                    not self.env[field.model]._auto or \
                    self.env[field.model]._transient:
                continue
            model_fields[field.relation] |= field

        # Map the models with their business names
        model_name = {field.model: field.model_id.name for field in all_fields}

        # Compute the references per record
        references = {record.id: [] for record in self}
        # Should be only one on the business flow, but who knows
        for res_model_name in res_models:
            records = self.filtered(lambda r: r.res_model_name == res_model_name)
            records_mapped = {record.res_id: record.id for record in records}
            reference_fields = model_fields[res_model_name]

            # Group the fields per model
            group_model_fields = {field.model: [] for field in reference_fields}
            for field in reference_fields:
                group_model_fields[field.model].append(field.name)


            for model in group_model_fields:
                ref_fields = group_model_fields[model]  # fields for the model
                domain = OR([[(f, 'in', records.mapped('res_id'))] for f in ref_fields])
                groupby_field = ref_fields[0]
                count_grouped = self.env[model].read_group(domain, [groupby_field], [groupby_field])
                for count in count_grouped:
                    if not count[groupby_field]:
                        continue
                    record_id = records_mapped.get(count[groupby_field][0])
                    if not record_id:
                        continue
                    references[record_id].append((count['%s_count' % groupby_field], model_name[model]))
        return references

    @api.depends('res_id')
    def _compute_usage(self):
        if ast.literal_eval(self.env['ir.config_parameter'].sudo().get_param('data_merge.compute_references', 'True')):
            references = self._get_references()
            for record in self:
                ref = references[record.id]
                record.used_in = ', '.join(['%s %s' % (r[0], r[1]) for r in ref])
        else:
            self.used_in = ''

    @api.depends('res_id')
    def _compute_fields(self):
        existing_records = {r.id:r for r in self._original_records().exists()}
        for record in self:
            original_record = existing_records.get(record.res_id) or self.env[record.res_model_name]
            name = original_record.display_name

            record.is_deleted = record.res_id not in existing_records.keys()
            record.name = name if name else '*Record Deleted*'
            record.record_create_date = original_record.create_date
            record.record_create_uid = original_record.create_uid.name or '*Deleted*'
            record.record_write_date = original_record.write_date
            record.record_write_uid = original_record.write_uid.name or '*Deleted*'

    @api.depends('is_deleted', 'is_discarded')
    def _compute_active(self):
        for record in self:
            record.active = not (record.is_deleted or record.is_discarded)

    def _original_records(self):
        if not self:
            return

        model_name = set(self.mapped('res_model_name')) or {}

        if len(model_name) != 1:
            raise ValidationError('Records must be of the same model')

        model = model_name.pop()
        ids = self.mapped('res_id')
        return self.env[model].with_context(active_test=False).sudo().browse(ids).exists()

    def _record_snapshot(self):
        """ Snapshot of the original record, to be logged in the chatter when merged """
        self.ensure_one()
        return self._render_values([])

    ############
    ### Helpers
    ############
    @api.model
    def _get_model_references(self, table):
        """
        Get all the foreign key referring to `table`.

        e.g. _get_model_references('res_company') -> {'res_partner': ['company_id']}

        :param str table: name of the table
        :returns a dict with table name as keys and the list of fields referenced as values
        :rtype: dict
        """
        query = """
            SELECT cl1.relname as table, array_agg(att1.attname) as columns
            FROM pg_constraint as con, pg_class as cl1, pg_class as cl2, pg_attribute as att1, pg_attribute as att2
            WHERE con.conrelid = cl1.oid
                AND con.confrelid = cl2.oid
                AND array_lower(con.conkey, 1) = 1
                AND con.conkey[1] = att1.attnum
                AND att1.attrelid = cl1.oid
                AND att2.attname = 'id'
                AND array_lower(con.confkey, 1) = 1
                AND con.confkey[1] = att2.attnum
                AND att2.attrelid = cl2.oid
                AND con.contype = 'f'
                AND cl2.relname = %s
            GROUP BY cl1.relname"""

        self.flush()
        self._cr.execute(query, (table, ))
        return {r[0]:r[1] for r in self._cr.fetchall()}

    @api.model
    def _update_foreign_keys(self, destination, source):
        """
        Update all the foreign keys referring to `source` records with `destination` as new referencee.
        The parameters are the real records and not data_merge.record

        :param destination: destination record of the foreign keys
        :param source: list of records
        """
        references = self._get_model_references(destination._table)

        source_ids = source.ids
        self.flush()

        for table, columns in references.items():
            for column in columns:
                query_dict = {
                    'table': table,
                    'column': column,
                }

                # Query to check the number of columns in the referencing table
                query = """SELECT COUNT(column_name) FROM information_schema.columns WHERE table_name ILIKE %s"""
                self._cr.execute(query, (table, ))
                column_count = self._cr.fetchone()[0]

                ## Relation table for M2M
                if column_count == 2:
                    # Retrieve the "other" column
                    query = """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE
                            table_name LIKE '%s'
                        AND column_name <> '%s'""" % (table, column)
                    self._cr.execute(query, ())
                    othercol = self._cr.fetchone()[0]
                    query_dict.update({'othercol': othercol})

                    for rec_id in source_ids:
                        # This query will filter out existing records
                        # e.g. if the record to merge has tags A, B, C and the master record has tags C, D, E
                        #      we only need to add tags A, B
                        query = """
                            UPDATE %(table)s o
                            SET %(column)s = %%(destination_id)s            --- master record
                            WHERE %(column)s = %%(record_id)s         --- record to merge
                            AND NOT EXISTS (
                                SELECT 1
                                FROM %(table)s i
                                WHERE %(column)s = %%(destination_id)s
                                AND i.%(othercol)s = o.%(othercol)s
                            )""" % query_dict

                        params = {
                            'destination_id': destination.id,
                            'record_id': rec_id,
                            'othercol': othercol
                        }
                        self._cr.execute(query, params)
                else:
                    query = """
                        UPDATE %(table)s o
                        SET %(column)s = %%(destination_id)s            --- master record
                        WHERE %(column)s = %%(record_id)s          --- record to merge
                    """ % query_dict
                    for rec_id in source_ids:
                        try:
                            with self._cr.savepoint():
                                params = {
                                    'destination_id': destination.id,
                                    'record_id': rec_id
                                }
                                self._cr.execute(query, params)
                        except psycopg2.IntegrityError as e:
                            # Failed update, probably due to a unique constraint
                            # updating fails, most likely due to a violated unique constraint
                            if psycopg2.errorcodes.UNIQUE_VIOLATION == e.pgcode:
                                _logger.warning('Query %s failed, due to an unique constraint', query)
                            else:
                                _logger.warning('Query %s failed', query)
                        except psycopg2.Error:
                            raise ValidationError('Query Failed.')

        self._merge_additional_models(destination, source_ids)
        destination.recompute()
        self.invalidate_cache()

    ## Manual merge of ir.attachment & mail.activity
    @api.model
    def _merge_additional_models(self, destination, source_ids):
        models_to_adapt = [
            {
                'table': 'ir_attachment',
                'id_field': 'res_id',
                'model_field': 'res_model',
            }, {
                'table': 'mail_activity',
                'id_field': 'res_id',
                'model_field': 'res_model',
            }, {
                'table': 'ir_model_data',
                'id_field': 'res_id',
                'model_field': 'model',
            }, {
                'table': 'mail_message',
                'id_field': 'res_id',
                'model_field': 'model',
            }, {
                'table': 'mail_followers',
                'id_field': 'res_id',
                'model_field': 'res_model',
            }
        ]
        query = """
            UPDATE %(table)s
            SET %(id_field)s = %%(destination_id)s
            WHERE %(id_field)s = %%(record_id)s
            AND %(model_field)s = %%(model)s"""
        for model in models_to_adapt:
            q = query % model
            for rec_id in source_ids:
                try:
                    with self._cr.savepoint():
                        params = {
                            'destination_id': destination.id,
                            'record_id': rec_id,
                            'model': destination._name
                        }
                        self._cr.execute(q, params)
                except psycopg2.IntegrityError as e:
                    # Failed update, probably due to a unique constraint
                    # updating fails, most likely due to a violated unique constraint
                    if psycopg2.errorcodes.UNIQUE_VIOLATION == e.pgcode:
                        _logger.warning('Query %s failed, due to an unique constraint', query)
                    else:
                        _logger.warning('Query %s failed', query)
                except psycopg2.Error:
                    raise ValidationError('Query Failed.')

    #############
    ### Override
    #############
    @api.model
    def create(self, vals):
        group = self.env['data_merge.group'].browse(vals.get('group_id', 0))
        record = self.env[group.res_model_name].browse(vals.get('res_id', 0))

        if not record.exists():
            raise ValidationError('The referenced record does not exist')
        return super(DataMergeRecord, self).create(vals)


    def write(self, vals):
        if 'is_master' in vals and vals['is_master']:
            master = self.with_context(active_test=False).group_id.record_ids.filtered('is_master')
            master.write({'is_master': False})

        return super(DataMergeRecord, self).write(vals)

    ############
    ### Actions
    ############
    def open_record(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': self.res_model_name,
            'res_id': self.res_id,
            'context': {
                'create': False,
                'edit': False
            }
        }
