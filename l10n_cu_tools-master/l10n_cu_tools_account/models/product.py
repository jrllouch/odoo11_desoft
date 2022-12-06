# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class ClassifierProductsCategoriesAccount(models.Model):
    _inherit = 'product.category'

    # Visible si el de arriba es verdadero
    property_tools_valuation = fields.Selection([
        ('manual', 'Manual'),
        ('automated', 'Automated'),
    ], 'Tools Valuation', company_dependent=True)

    property_amortization_methods = fields.Selection([
        ('50', '50% at the start and 50% at the end'),
        ('100in', '100% at the beginning'),
        ('100out', '100% at the end'),
        ('periodic', '% Periodic'),
    ], 'Amortization Methods', company_dependent=True)

    property_tool_input_account = fields.Many2one('account.account', string='Tool Input Account',
                                                  company_dependent=True)
    property_tool_output_account = fields.Many2one('account.account', string='Tool Output Account',
                                                   company_dependent=True)
    property_tool_missing_account = fields.Many2one('account.account', string='Tool Missing Account',
                                                    company_dependent=True)
    property_tool_surplus_account = fields.Many2one('account.account', string='Tool Surplus Account',
                                                    company_dependent=True)
    property_tool_valoration_account = fields.Many2one('account.account', string='Tool Valoration Account',
                                                       company_dependent=True)
    property_tool_amortization_account = fields.Many2one('account.account', string='Tool Amortization Account',
                                                         company_dependent=True)
    property_tool_journal = fields.Many2one('account.journal', domain=[('type', '=', 'general')], string='Tool Journal',
                                            company_dependent=True)

    @api.multi
    def write(self, values):
        if 'property_amortization_methods' in values:
            for rec in self:
                template = rec.env['product.template'].search([('categ_id', '=', rec.id)]).mapped('id')
                products = rec.env['product.product'].search([('product_tmpl_id', 'in', template)]).mapped('id')
                quant = rec.env['tools.quant'].search([('product_id', 'in', products)], limit=1)
                if quant:
                    raise UserError(_(
                        'You can not change the method of wear if you have products with stocks.'))
        return super(ClassifierProductsCategoriesAccount, self).write(values)


class Product(models.Model):
    _inherit = "product.product"

    tools_value = fields.Float(
        'Value', compute='_tools_compute_quantities')

    @api.depends('tools_move_ids.product_qty', 'tools_move_ids.state')
    def _tools_compute_quantities(self):
        tools_values = super(Product, self)._tools_compute_quantities()
        for product in self:
            if product.id in tools_values:
                product.tools_value = tools_values[product.id][1]
