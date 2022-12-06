# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, exceptions, fields, models, _


class Company(models.Model):
    _inherit = 'res.company'

    stock_type_id = fields.Many2one(
        'tools.picking.type', 'Stock Operation Type',
        domain=[('code', '=', 'stock_operation')])

    @api.model
    def create(self, values):
        for company in self:
            company._create_tools_picking_type()
            company.stock_type_id.active = True
        return super(Company, self).create(values)

    @api.multi
    def write(self, vals):
        for company in self:
            if not company.stock_type_id and not vals.get("stock_type_id"):
                company._create_tools_picking_type()
                company.stock_type_id.active = True
        return super(Company, self).write(vals)

    def _create_tools_picking_type(self):
        picking_type_obj = self.env['tools.picking.type']
        seq_obj = self.env['ir.sequence']
        for company in self:
            # man_seq_id = seq_obj.sudo().create('name': company.name + _(' Sequence Manufacturing'), 'prefix': company.code + '/MANU/', 'padding')
            seq = seq_obj.search([('code', '=', 'tools')], limit=1)
            other_pick_type = picking_type_obj.search([('company_id', '=', company.id)], order = 'sequence desc', limit=1)
            color = other_pick_type.color if other_pick_type else 0
            max_sequence = other_pick_type and other_pick_type.sequence or 0
            stock_type = picking_type_obj.create({
                'name': _('Stock Outgoing'),
                'company_id': company.id,
                'code': 'stock_operation',
                'sequence_id': seq.id,
                'sequence': max_sequence,
                'color': color})
            company.write({'stock_type_id': stock_type.id})