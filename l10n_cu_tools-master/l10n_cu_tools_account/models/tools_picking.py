# -*- coding: utf-8 -*-

# Part of Desoft. See LICENSE file for full copyright and licensing details.

# List of contributors:
# Bernardo Justiz González bernardo.justiz@cmw.desoft.cu

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ToolsPicking(models.Model):
    _inherit = 'tools.picking'

    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account')

    @api.multi
    def quant_outgoing_update(self, move):
        super(ToolsPicking, self).quant_outgoing_update(move)
        quant = self.env['tools.quant'].search([('product_id', '=', move.product_id.id), (
            'custodian_id', '=', move.custodian_orig_id.id)], limit=1).sorted(
            key=lambda r: r.in_date)
        if quant.exists():
            quant.value -= move.product_qty * move.price_unit
            if move.product_tmpl_id.categ_id.property_amortization_methods == '50':
                quant.amortization -= move.product_qty * move.price_unit / 2
            elif move.product_tmpl_id.categ_id.property_amortization_methods == '100in':
                quant.amortization -= move.product_qty * move.price_unit

    @api.multi
    def quant_income_update(self, move):
        super(ToolsPicking, self).quant_income_update(move)
        quant = self.env['tools.quant'].search([('product_id', '=', move.product_id.id),
                                                ('custodian_id', '=', move.custodian_dest_id.id),
                                                ('price', '=', move.price_unit)])
        quant.value += move.product_qty * move.price_unit
        if move.product_tmpl_id.categ_id.property_amortization_methods == '50':
            quant.amortization += move.product_qty * move.price_unit / 2
        elif move.product_tmpl_id.categ_id.property_amortization_methods == '100in':
            quant.amortization += move.product_qty * move.price_unit

    @api.multi
    def button_validate(self):
        for move in self.move_lines:
            if move.product_id.categ_id.property_valuation not in 'manual_periodic':
                move._account_entry_move()
            move.state = 'done'
        self.state = 'done'
        return True

    @api.onchange('custodian_dest_id')
    def _onchange_custodian_dest_id(self):
        if self.custodian_dest_id != False:
            self.analytic_account_id = self.custodian_dest_id.analytic_account

    @api.onchange('custodian_orig_id')
    def _onchange_custodian_orig_id(self):
        if self.custodian_orig_id != False:
            self.analytic_account_id = self.custodian_orig_id.analytic_account
