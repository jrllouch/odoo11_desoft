# -*- coding: utf-8 -*-

# Part of Desoft. See LICENSE file for full copyright and licensing details.

# List of contributors:
# Bernardo Justiz González bernardo.justiz@cmw.desoft.cu

from odoo import api, fields, models, _


CUSTODIAN_MODEL = [
    ('res.partner', 'Contact'),
]

class Custodian(models.Model):
    _name = "tools.custodian"
    _description = "Tools Custodian"
    _order = "name"


    name = fields.Char(
        'Custodian Name',
        compute='_compute_complete_name',
        store=True
        )
    custodian_id = fields.Reference(
        selection=CUSTODIAN_MODEL,
        required=True
        )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        index=True,
        default=lambda self: self.env['res.company']._company_default_get('tools.custodian')
        )
    active = fields.Boolean(
        'Active',
        default=True,
        help="If unchecked, it will allow you to hide the custodian without removing it."
        )

    _sql_constraints = [
        ('default_custodian_name_company_uniq', 'unique(name, company_id)',
         'The name of the tools custodian must be unique in company!'),
    ]

    @api.depends('custodian_id')
    def _compute_complete_name(self):
        for custodian in self:
            custodian.name = custodian.custodian_id.name