# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp


class ClassifierProductsCategories(models.Model):
    _inherit = 'product.category'

    tool_category = fields.Boolean('Tool Category', default=False,
                                   help="Informs if the category of products will be used or not by tools and "
                                        "tools in use.")


class Product(models.Model):
    _inherit = "product.product"

    tools_quant_ids = fields.One2many('tools.quant', 'product_id', help='Technical: used to compute quantities.')
    tools_move_ids = fields.One2many('tools.move', 'id', help='Technical: used to compute quantities.')
    tools_qty_available = fields.Float(
        'Tools On Hand', compute='_tools_compute_quantities',
        digits=dp.get_precision('Product Unit of Measure'),
        help="Current quantity of products.\n"
             "In a context with a single Stock Location, this includes "
             "goods stored at this Location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods stored in the Stock Location of this Warehouse, or any "
             "of its children.\n"
             "stored in the Stock Location of the Warehouse of this Shop, "
             "or any of its children.\n"
             "Otherwise, this includes goods stored in any Stock Location "
             "with 'internal' type.")

    def action_view_tools_move(self):
        self.ensure_one()
        action = self.env.ref('l10n_cu_tools.tools_move_action').read()[0]
        action['domain'] = [('product_id', '=', self.id)]
        return action

    @api.depends('tools_move_ids.product_qty', 'tools_move_ids.state')
    def _tools_compute_quantities(self):
        to_date = self.env.context.get('to_date')
        if to_date:
            query = """SELECT tm.product_id, SUM(CASE WHEN tm.custodian_orig_id ISNULL THEN tm.product_qty ELSE 
                                                  -tm.product_qty END), SUM(CASE WHEN tm.custodian_orig_id ISNULL THEN
                                                  tm.price_unit*tm.product_qty ELSE - tm.price_unit*tm.product_qty END)
                               FROM tools_move AS tm 
                               WHERE tm.date <= %s AND tm.state = 'done' AND tm.company_id = %s AND 
                                      (tm.custodian_orig_id ISNULL OR tm.custodian_dest_id ISNULL)
                               GROUP BY tm.product_id"""
            params = (to_date, self.env.user.company_id.id)
        else:
            query = """SELECT tq.product_id, SUM(tq.quantity), SUM(tq.quantity*tq.price)
                               FROM tools_quant AS tq
                               WHERE tq.company_id = %s
                               GROUP BY tq.product_id"""
            params = (self.env.user.company_id.id,)
        self.env.cr.execute(query, params=params)
        res = self.env.cr.fetchall()
        tools_values = {rec[0]: (rec[1], rec[2]) for rec in res}
        for product in self:
            if product.id in tools_values:
                product.tools_qty_available = tools_values[product.id][0]
        return tools_values


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    type = fields.Selection(selection_add=[('product', 'Stockable Product')])
    tool_category = fields.Boolean(related='categ_id.tool_category')
    tools_qty_available = fields.Float(
        'Tools On Hand', compute='_tools_compute_quantities',
        digits=dp.get_precision('Product Unit of Measure'),
        help="Current quantity of products.\n"
             "In a context with a single Stock Location, this includes "
             "goods stored at this Location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods stored in the Stock Location of this Warehouse, or any "
             "of its children.\n"
             "stored in the Stock Location of the Warehouse of this Shop, "
             "or any of its children.\n"
             "Otherwise, this includes goods stored in any Stock Location "
             "with 'internal' type.")

    def _tools_compute_quantities(self):
        for template in self.product_variant_ids:
            self.tools_qty_available += template.tools_qty_available

    def action_view_tools_move(self):
        self.ensure_one()
        action = self.env.ref('l10n_cu_tools.tools_move_action').read()[0]
        action['domain'] = [('product_id.product_tmpl_id', 'in', self.ids)]
        return action

    def tools_action_open_quants(self):
        products = self.mapped('product_variant_ids')
        action = self.env.ref('l10n_cu_tools.tools_product_open_quants').read()[0]
        action['domain'] = [('product_id', 'in', products.ids)]
        return action
