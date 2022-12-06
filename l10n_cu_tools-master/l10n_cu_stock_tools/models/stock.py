# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Location(models.Model):
    _inherit = "stock.location"

    is_tools_location = fields.Boolean(string='Tools in use')


class Picking(models.Model):
    _inherit = 'stock.picking'

    location_id_usage = fields.Boolean(
        related='location_id.is_tools_location', string='Is a tools out'
    )

    location_dest_usage = fields.Boolean(
        related='location_dest_id.is_tools_location', string='Is a tools entry'
    )

    custodian_orig_id = fields.Many2one(
        'tools.custodian'
    )

    custodian_dest_id = fields.Many2one(
        'tools.custodian'
    )

    code = fields.Selection([
        ('not in tools', 'Not is a tools operation'),
        ('income', 'Entrance'),
        ('income_surplus', 'Entry for Surplus'),
        ('outgoing', 'Out'),
        ('outgoing_Missing', 'Out for Missing'),
        ('internal', 'Internal Transfer'),
        ('income_transfer', 'Income Dependencies Transfer'),
        ('outgoing_transfer', 'Outgoing Dependencies Transfer'),
    ], default='not in tools')

    @api.onchange('move_line_ids')
    def onchange_move_line(self):
        for line in self.move_line_ids:
            if line.location_id.is_tools_location:
                self.location_id_usage = True
                if self.picking_type_id.code == 'outgoing':
                    self.code = 'outgoing'
            if line.location_dest_id.is_tools_location:
                self.location_dest_usage = True
                if self.picking_type_id.code == 'incoming':
                    self.code = 'income'
            if line.location_id.is_tools_location and line.location_dest_id.is_tools_location:
                self.location_id_usage = True
                self.location_dest_usage = True
                if self.picking_type_id.code == 'internal':
                    self.code = 'internal'
            if not line.location_id.is_tools_location and not line.location_dest_id.is_tools_location:
                self.code = 'not in tools'
            if not line.product_id.categ_id.tool_category and self.code != 'not in tools':
                raise UserError(_('This operation is only for tools product'))
        if not self.move_line_ids:
            self.location_id_usage = False
            self.location_dest_usage = False
            self.code = 'not in tools'

    def button_validate(self):
        res_super = super(Picking, self).button_validate()
        ToolsPicking = self.env['tools.picking']
        ToolsPickingtype = self.env['tools.picking.type']

        if self.code == 'not in tools':
            return res_super

        if self.location_dest_id.is_tools_location or self.location_id.is_tools_location:
            if not (ToolsPickingtype.search(
                    [('code', '=', self.code), ('company_id', '=', self.company_id.id)],
                    limit=1)):
                raise UserError(_('You cannot validate inventory, you need to update the types of operations'))

            res = {
                'picking_type_id': ToolsPickingtype.search(
                    [('code', '=', self.code), ('company_id', '=', self.company_id.id)], limit=1).id,
                'custodian_orig_id': self.custodian_orig_id.id or None,
                'custodian_dest_id': self.custodian_dest_id.id or None,
                'state': 'draft',
                'origin': self.name,
                'date': self.date,
                'company_id': self.company_id.id,
            }

            picking = ToolsPicking.create(res)
            move_line = []
            for move in self.move_lines:
                ToolMove = self.env['tools.move']
                tools_line = {
                    'name': move.reference,
                    'sequence': move.sequence,
                    'date': move.date,
                    'company_id': move.company_id.id,
                    'picking_id': picking.id,
                    'picking_type_id': ToolsPickingtype.search(
                        [('code', '=', self.code), ('company_id', '=', move.company_id.id)], limit=1).id,
                    'custodian_orig_id': self.custodian_orig_id.id or None,
                    'custodian_dest_id': move.picking_id.custodian_dest_id.id or None,
                    'product_id': move.product_id.id,
                    'product_tmpl_id': move.product_tmpl_id.id,
                    'product_uom': move.product_uom.id,
                    'product_uom_qty': move.product_uom_qty,
                    'price_unit': move.product_id.standard_price,
                    'state': 'done',
                    'origin': move.origin,
                    'reference': move.reference,
                    'note': move.note,
                }
                move_line_tools = ToolMove.sudo().create(tools_line)

                move.write({'tool_move_id': move_line_tools.id})
                move_line.append(move_line_tools.id)

            picking.write({'move_line': move_line})

            picking.action_confirm()
            return res_super
        else:
            return res_super
