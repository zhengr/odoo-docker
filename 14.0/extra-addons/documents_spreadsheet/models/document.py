# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.tools import image_process

class Document(models.Model):
    _inherit = 'documents.document'

    handler = fields.Selection([('spreadsheet', 'Spreadsheet')], ondelete={'spreadsheet': 'cascade'})
    raw = fields.Binary(related='attachment_id.raw', readonly=False)
    # TODO extend the versioning system to use raw.

    @api.model_create_multi
    def create(self, vals_list):
        default_folder = self.env.ref('documents_spreadsheet.documents_spreadsheet_folder', raise_if_not_found=False)
        if not default_folder:
            default_folder = self.env['documents.folder'].search([], limit=1, order="sequence asc")
        for vals in vals_list:
            if vals.get('handler') == 'spreadsheet':
                vals['folder_id'] = vals.get('folder_id', default_folder.id)
                if 'thumbnail' in vals:
                    vals['thumbnail'] = image_process(vals['thumbnail'], size=(80, 80), crop='center')
        documents = super().create(vals_list)
        for document in documents:
            if document.handler == 'spreadsheet':
                self.env['spreadsheet.contributor']._update(self.env.user, document)
        return documents

    def write(self, vals):
        for document in self:
            if document.handler == 'spreadsheet':
                self.env['spreadsheet.contributor']._update(self.env.user, document)
        return super().write(vals)

    @api.depends('checksum', 'handler')
    def _compute_thumbnail(self):
        # Spreadsheet thumbnails cannot be computed from their binary data.
        # They should be saved independently.
        spreadsheets = self.filtered(lambda d: d.handler == 'spreadsheet')
        super(Document, self - spreadsheets)._compute_thumbnail()

    @api.model
    def get_spreadsheets_to_display(self):
        self.check_access_rights('read')
        self.flush(['name'])
        self.env['spreadsheet.contributor'].flush()
        self.env.cr.execute("""
            SELECT DD.id, DD.name
            FROM documents_document DD
            LEFT JOIN spreadsheet_contributor SC on DD.id = SC.document_id and SC.user_id = %(user_id)s
            WHERE DD.handler = 'spreadsheet' AND DD.active
            ORDER BY SC.last_update_date DESC, DD.write_date DESC
         """, { 'user_id': self.env.user.id })
        result = self.env.cr.dictfetchall()
        documents = self.browse([d['id'] for d in result])
        documents.check_field_access_rights('read', ['name'])
        documents.check_access_rule('read')
        return result
