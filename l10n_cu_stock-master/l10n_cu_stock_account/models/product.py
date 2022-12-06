# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, pycompat


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.remaining_value',
                 'product_tmpl_id.cost_method', 'product_tmpl_id.standard_price', 'product_tmpl_id.property_valuation',
                 'product_tmpl_id.categ_id.property_valuation')
    def _compute_stock_value(self):
        to_date = self.env.context.get('to_date')
        location_id = self.env.context.get('location_id')

        if to_date:
            query = """SELECT sml.product_id, SUM(CASE WHEN sl2.usage = 'internal' THEN sml.qty_done ELSE
                                  - sml.qty_done END), SUM(sml.qty_done * sm.price_unit)
                        FROM stock_move AS sm LEFT JOIN stock_move_line as sml ON sm.id = sml.move_id
                                LEFT JOIN stock_location AS sl ON sml.location_id = sl.id
                                LEFT JOIN stock_location AS sl2 ON sml.location_dest_id = sl2.id
                        WHERE sm.date <= %s AND sm.state = 'done' AND
                                ((sl.company_id IS NULL AND sl2.company_id = %s) OR
                                (sl.company_id = %s AND sl2.company_id IS NULL)) AND
                                ((sl.usage = 'internal' AND sl2.usage != 'internal') OR
                                (sl.usage != 'internal' AND sl2.usage = 'internal')) """
            if location_id:
                query = query + 'AND (sml.location_id = %s OR sml.location_dest_id = %s) ' % (location_id, location_id)
            query = query + """GROUP BY sml.product_id"""
            params = (to_date, self.env.user.company_id.id, self.env.user.company_id.id)
        else:
            query = """SELECT sq.product_id, SUM(sq.quantity), SUM(sq.value)
                       FROM stock_quant AS sq LEFT JOIN stock_location AS sl ON sq.location_id = sl.id
                       WHERE sq.company_id = %s AND sl.usage = 'internal' """
            if location_id:
                query = query + 'AND sq.location_id = %s ' % location_id
            query = query + """GROUP BY sq.product_id"""
            params = (self.env.user.company_id.id,)

        self.env.cr.execute(query, params=params)
        res = self.env.cr.fetchall()
        products_values = {rec[0]: (rec[1], rec[2]) for rec in res}
        if products_values:
            for product in self:
                if product.id in products_values:
                    product.qty_at_date = products_values[product.id][0]
                    product.stock_value = products_values[product.id][1]

    @api.multi
    def do_change_standard_price(self, new_price, account_id):
        """ Changes the Standard Price of Product and creates an account move accordingly."""
        AccountMove = self.env['account.move']
        StockMove = self.env['stock.move']

        quant_locs = self.env['stock.quant'].sudo().read_group([('product_id', 'in', self.ids)], ['location_id'], ['location_id'])
        quant_loc_ids = [loc['location_id'][0] for loc in quant_locs]
        locations = self.env['stock.location'].search([('usage', '=', 'internal'), ('company_id', '=', self.env.user.company_id.id), ('id', 'in', quant_loc_ids)])

        product_accounts = {product.id: product.product_tmpl_id.get_product_accounts() for product in self}

        for location in locations:
            for product in self.with_context(location=location.id, compute_child=False).filtered(lambda r: r.valuation == 'real_time'):
                diff = product.standard_price - new_price
                if float_is_zero(diff, precision_rounding=product.currency_id.rounding):
                    raise UserError(_("No difference between standard price and new price!"))
                if not product_accounts[product.id].get('stock_valuation', False):
                    raise UserError(_('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))
                qty_available = product.qty_available
                if qty_available:
                    # Accounting Entries
                    if diff * qty_available > 0:
                        debit_account_id = account_id
                        credit_account_id = product_accounts[product.id]['stock_valuation'].id
                    else:
                        debit_account_id = product_accounts[product.id]['stock_valuation'].id
                        credit_account_id = account_id

                    move_vals = {
                        'journal_id': product_accounts[product.id]['stock_journal'].id,
                        'company_id': location.company_id.id,
                        'line_ids': [(0, 0, {
                            'name': _('Standard Price changed  - %s') % (product.display_name),
                            'account_id': debit_account_id,
                            'debit': abs(diff * qty_available),
                            'credit': 0,
                            'product_id': product.id,
                        }), (0, 0, {
                            'name': _('Standard Price changed  - %s') % (product.display_name),
                            'account_id': credit_account_id,
                            'debit': 0,
                            'credit': abs(diff * qty_available),
                            'product_id': product.id,
                        })],
                    }
                    move = AccountMove.create(move_vals)
                    move.post()

                    stock_move_vals = {
                        'name': _('Standard Price changed  - %s') % (product.display_name),
                        'product_id': product.id,
                        'product_uom_qty': 0,
                        'product_uom': product.uom_id.id,
                        'location_id': diff < 0 and product.property_stock_inventory.id or location.id,
                        'location_dest_id': diff < 0 and location.id or product.property_stock_inventory.id,
                        'state': 'done',
                        'value': -diff * qty_available
                    }
                    stock_move = StockMove.create(stock_move_vals)

        self.write({'standard_price': new_price})
        return True
