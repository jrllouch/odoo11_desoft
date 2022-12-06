# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.addons.l10n_cu_tools.models.tools_custodian import CUSTODIAN_MODEL


CUSTODIAN_MODEL.extend([
    ('tools.storage', 'Storeroom')
])


class ToolsStorage(models.Model):
    _name = 'tools.storage'

    name = fields.Char('Name', index=True, required=True, translate=True)

    default_code = fields.Char('Code', required=True)

    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env['res.company']._company_default_get('l10n_cu_tools_storage.tools_storage'),
        index=1)

    active = fields.Boolean('Active', default=True,
                            help="If unchecked, it will allow you to hide the storage without removing it.")

    # image: all image fields are base64 encoded and PIL-supported

    image = fields.Binary(
        "Image", attachment=True,
        help="This field holds the image used as image for the tools storage, limited to 1024x1024px.")

    image_medium = fields.Binary(
        "Medium-sized image", attachment=True,
        help="Medium-sized image of the the tools storage. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved, "
             "only when the image exceeds one of those sizes. Use this field in form views or some kanban views.")

    image_small = fields.Binary(
        "Small-sized image", attachment=True,
        help="Small-sized image of the the tools storage. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)',
         'The name of the tools storage must be unique in company!'),
        ('default_code_company_uniq', 'unique(default_code, company_id)',
         'The code of the tools storage must be unique in company!'),
    ]

    @api.model
    def create(self, vals):
        ts = super(ToolsStorage, self).create(vals)
        self.env['tools.custodian'].create({
                    'name': 'name' in vals and vals['name'] or '',
                    'custodian_id': _('tools.storage,') + str(ts.id),
                    'company_id': 'company_id' in vals and vals['company_id'] or 0,
                    'active': 'True',
                })
        return ts

    @api.multi
    def write(self, vals):
        ts = super(ToolsStorage, self).write(vals)
        storeroom = self.env['tools.custodian'].search([('custodian_id', '=', _('tools.storage,') + str(self.id))])
        if vals.get('name'):
            storeroom.write({
                        'name': vals['name'],
                    })
        if 'active' in vals:
            storeroom.write({
                        'active': vals['active'],
                    })
        return ts

    @api.multi
    def unlink(self):
        domain = [
        ]
        for storeroom in self:
            domain.extend([
                _('tools.storage,') + str(storeroom.id)
            ])
        custodian = self.env['tools.custodian'].search([('custodian_id', 'in',domain)])
        custodian.unlink()

        return super(ToolsStorage, self).unlink()