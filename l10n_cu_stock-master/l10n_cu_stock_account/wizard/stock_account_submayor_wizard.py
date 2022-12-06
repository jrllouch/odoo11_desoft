# -*- coding: utf-8 -*-
from odoo import models, api, fields
from odoo.addons import decimal_precision as dp


class l10n_cu_stock_account_submayor_wizard(models.TransientModel):
    _name = 'stock.account.submayor.wizard'
    _description = 'Stock submayor'

    date_start = fields.Datetime('Date start', default=fields.Date.today(), required=True)
    date_stop = fields.Datetime('Date stop', default=fields.Date.today(), required=True)
    account_ids = fields.Many2many('account.account', string='Account')
    product_ids = fields.Many2many('product.product', string='Product')
    location_ids = fields.Many2many('stock.location', string='Location', domain="[('usage', '=', 'internal')]")

    @api.onchange('account_ids')
    def onchange_account_ids(self):
        if self.account_ids:
            self.product_ids = False
            prods = self.env['product.product'].search([('product_tmpl_id.categ_id.property_stock_valuation_account_id',
                                                       'in', self.account_ids.ids)], order='id asc')
            return {
                'domain': {'product_ids': [('id', 'in', prods.ids)]}
            }
        else:
            return {
                'domain': {'product_ids': []}
            }

    def prod_by_acc(self, product_ids=False):
        res = {}
        if not product_ids:
            product_ids = self.env['product.product'].search([], order='id asc')
        for prod in product_ids:
            acc = self.env['account.account'].search([('id', '=', prod.categ_id.property_stock_valuation_account_id.id)])
            if acc not in res:
                res[acc] = [prod]
            else:
                res[acc].append(prod)
        return res

    def mov_by_loc(self, product_id):
        res = {}
        domain = [('date', '>=', self.date_start), ('date', '<=', self.date_stop), ('state', '=', 'done'),
                  ('product_id', '=', product_id.id)]
        if self.location_ids:
            res = self.auxiliary_method(product_id, domain, self.location_ids)
        else:
            locations = self.env['stock.location'].search([('usage', '=', 'internal'), ('active', '=', True)])
            res = self.auxiliary_method(product_id, domain, locations)
        return res

    def auxiliary_method(self, product_id, domain, locations):
        res = {}
        for locat in locations:
            domain.append('|')
            domain.append(('location_id', '=', locat.id))
            domain.append(('location_dest_id', '=', locat.id))
            move_lines = self.env['stock.move.line'].search(domain)
            domain.pop(4)
            domain.pop(4)
            domain.pop(4)
            if move_lines:
                new_product_id = product_id.with_context(to_date=self.date_start, location_id=locat.id)
                for ml in move_lines:
                    if locat not in res:
                        res[locat] = {'value': (new_product_id.qty_at_date, new_product_id.stock_value),
                                      'move_lines': [ml]}
                    else:
                        res[locat]['move_lines'].append(ml)
        return res

    @api.multi
    def print_report(self):
        report_name = "l10n_cu_stock_account.l10n_cu_action_report_stock_submayor"
        if self.env.context.get('to_html'):
            report_name = "l10n_cu_stock_account.l10n_cu_action_report_html_stock_submayor"
        return self.env.ref(report_name).report_action(self, config=False)
