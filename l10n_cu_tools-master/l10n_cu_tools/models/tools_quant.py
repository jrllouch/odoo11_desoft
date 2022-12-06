# -*- coding: utf-8 -*-

# Part of Desoft. See LICENSE file for full copyright and licensing details.

# List of contributors:
# Bernardo Justiz González bernardo.justiz@cmw.desoft.cu

from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import UserError


class ToolsQuant(models.Model):
    _name = 'tools.quant'
    _description = "Tools Quant"
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', 'Product', ondelete='restrict',
                                 readonly=True, required=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template',
                                      related='product_id.product_tmpl_id')
    product_uom_id = fields.Many2one('product.uom', 'Unit of Measure', readonly=True,
                                     related='product_id.uom_id')
    company_id = fields.Many2one('res.company', string='Company', store=True,
                                 readonly=True, default=lambda self: self.env.user.company_id)
    custodian_id = fields.Many2one(
        'tools.custodian',
        string="Custodian",
        required=True)
    quantity = fields.Float('Quantity',
                            help='Quantity of products in this quant, in the default unit of measure of the tools',
                            readonly=True, required=True)
    price = fields.Float('Tools Price',
                         help="Cost used for tools valuation in standard price"
                              "Expressed in the default unit of measure of the tools.")
    in_date = fields.Datetime('Inventory Date', readonly=True)
    percent_save_point = fields.Integer(help='Mark inventory percent status', default=0)

    @api.multi
    @api.constrains('quantity')
    def _check_quantity(self):
        '''
        Verify that the quantity of the quant be > 0.
        '''
        if self.quantity < 0:
            raise UserError(_("Cannot extract more than the existing amount for the product %s"
                              ) % (self.product_id.name,))

    @api.multi
    @api.constrains('price')
    def _check_price(self):
        '''
        Verify that the price of the quant be > 0.
        '''

        if self.company_id.currency_id.is_zero(self.price):
            raise UserError(_("The cost of %s is currently equal to 0. Change the cost or the configuration of your "
                              "product to avoid an incorrect valuation.") % (self.product_id.name,))

    def _gather(self, product_id, custodian_id,  strict=False):

        domain = [
            ('product_id', '=', product_id.id),
        ]
        domain = expression.AND([[('custodian_id', '=', custodian_id.id)], domain])

        # Copy code of _search for special NULLS FIRST/LAST order
        self.sudo(self._uid).check_access_rights('read')
        query = self._where_calc(domain)
        self._apply_ir_rules(query, 'read')
        from_clause, where_clause, where_clause_params = query.get_sql()
        where_str = where_clause and (" WHERE %s" % where_clause) or ''
        query_str = 'SELECT "%s".id FROM ' % self._table + from_clause + where_str
        # query_str = 'SELECT "%s".id FROM ' % self._table + from_clause + where_str + " ORDER BY "+ removal_strategy_order
        self._cr.execute(query_str, where_clause_params)
        res = self._cr.fetchall()
        # No uniquify list necessary as auto_join is not applied anyways...
        return self.browse([x[0] for x in res])