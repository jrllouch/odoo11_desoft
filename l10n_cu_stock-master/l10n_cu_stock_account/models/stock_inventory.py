# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp


class Inventory(models.Model):
    _inherit = "stock.inventory"

    stock_inventory_picking_in = fields.Many2one('stock.picking.type', 'Picking Type In', readonly=True, required=False,
                                                 states={'confirm': [('readonly', False), ('required', True)]},
                                                 domain="[('default_location_dest_id', '=', location_id)]")
    stock_inventory_picking_out = fields.Many2one('stock.picking.type', 'Picking Type Out', readonly=True, required=False,
                                                  states={'confirm': [('readonly', False), ('required', True)]},
                                                  domain="[('default_location_src_id', '=', location_id)]")
    import_total = fields.Float('Import Total', digits=dp.get_precision('Product Unit of Measure'),
                                compute='_get_total_import')
    percent_number = fields.Integer('Product Percent', default=10)

    @api.one
    @api.constrains('date')
    def _check_date(self):
        if self.company_id.inventory_lock_date:
            if self.date[:10] <= self.company_id.inventory_lock_date:
                raise ValidationError(_('The date: %s, must be greater than the inventory lock date: %s')
                                      % (self.date[:10], self.company_id.inventory_lock_date))

    def post_inventory(self):
        super(Inventory, self).post_inventory()
        StockPicking = self.env['stock.picking']
        Pickingtype = self.env['stock.picking.type']
        for inv in self:
            move_in = inv.mapped('move_ids').filtered(lambda move: move.state == 'done' and move.location_dest_id.usage == 'internal')
            move_out = inv.mapped('move_ids').filtered(lambda move: move.state == 'done' and move.location_id.usage == 'internal')
            if move_out:
                res = {
                    'picking_type_id': inv.stock_inventory_picking_out.id or Pickingtype.search([('template.code', '=', 'ai'), ('warehouse_id.id', '=', inv.location_id.get_warehouse().id)], limit=1).id,
                    'location_id': inv.location_id.id,
                    'location_dest_id': move_out[0].product_id.property_stock_inventory.id,
                    'state': 'pending',
                    'origin': inv.name,
                    'date': inv.date,
                }
                picking = StockPicking.create(res)
                move_out.write({'picking_id': picking.id, 'date': inv.date})
                move_line_out = move_out.mapped('move_line_ids').filtered(lambda move: move.state == 'done' and move.location_id.usage == 'internal')
                move_line_out.write({'picking_id': picking.id, 'date': inv.date})
            if move_in:
                res = {
                    'picking_type_id': inv.stock_inventory_picking_in.id or Pickingtype.search([('template.code', '=', 'ai'), ('warehouse_id.id', '=', inv.location_id.get_warehouse().id)], limit=1).id,
                    'location_id': move_in[0].product_id.property_stock_inventory.id,
                    'location_dest_id': inv.location_id.id,
                    'state': 'pending',
                    'origin': inv.name,
                    'date': inv.date,
                }
                picking = StockPicking.create(res)
                move_in.write({'picking_id': picking.id, 'date': inv.date})
                move_line_in = move_in.mapped('move_line_ids').filtered(lambda move: move.state == 'done' and move.location_dest_id.usage == 'internal')
                move_line_in.write({'picking_id': picking.id, 'date': inv.date})

    @api.one
    @api.depends('product_id', 'line_ids.import_physical_count', 'line_ids.import_theoretical_count',
                 'line_ids.import_surplus')
    def _get_total_import(self):
        """ For single product inventory, total quantity of the counted """
        total_import_physical_count = 0.0
        total_import_theoretical_count = 0.0
        total_import_surplus = 0.0
        if self.product_id:
            total_import_physical_count += sum(self.mapped('line_ids').mapped('import_physical_count'))
            total_import_theoretical_count += sum(self.mapped('line_ids').mapped('import_theoretical_count'))
            total_import_surplus += sum(self.mapped('line_ids').mapped('import_surplus'))
            self.import_total = total_import_physical_count + total_import_theoretical_count + total_import_surplus
        else:
            self.import_total = 0.0
    @api.model
    def _selection_filter(self):
        """ Get the list of filter allowed according to the options checked
        in 'Settings\Warehouse'. """
        res = super(Inventory, self)._selection_filter()
        res.append(['percent', _('By Percent')])
        return res

    def action_done(self):
        for inv in self:
            Quant = inv.env['stock.quant']
            for line in inv.line_ids:
                qs = Quant._gather(line.product_id, line.location_id, line.prod_lot_id, line.package_id, owner_id=None, strict=True)
                for q in qs:
                    q.percent_save_point += 1
        return super(Inventory, self).action_done()

    def _get_inventory_lines_values(self):
        # _get_inventory_stolen
        locations = self.env['stock.location'].search([('id', 'child_of', [self.location_id.id])])
        args = tuple(locations.ids)
        vals = []
        Product = self.env['product.product']
        quant_products = self.env['product.product']

        if self.filter == 'percent':
            #Hago el select de todos los quants, no borre el group_by ya que el al borrarlo me da un error:
            self.env.cr.execute("""SELECT COUNT(*)
                                FROM stock_quant
                                LEFT JOIN product_product
                                ON product_product.id = stock_quant.product_id
                                WHERE location_id in %s""", (args,))
            q = self.env.cr.dictfetchall()
            limit = round(self.percent_number * q[0]['count']/100, 0)
            # Hago el select de los quants limitado por el numero del porciento, no borre el group_by ya que el al borrarlo me da un error:
            self.env.cr.execute("""SELECT product_id, sum(quantity) as product_qty, location_id, lot_id as prod_lot_id, package_id, owner_id as partner_id
                                            FROM stock_quant
                                            LEFT JOIN product_product
                                            ON product_product.id = stock_quant.product_id
                                            WHERE location_id in %s
                                            GROUP BY product_id, location_id, lot_id, package_id, partner_id 
                                            LIMIT %s""", (args, int(limit)))
            # Lleno vals[]
            for product_data in self.env.cr.dictfetchall():
                # replace the None the dictionary by False, because falsy values are tested later on
                for void_field in [item[0] for item in product_data.items() if item[1] is None]:
                    product_data[void_field] = False
                product_data['theoretical_qty'] = product_data['product_qty']
                if product_data['product_id']:
                    product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
                    quant_products |= Product.browse(product_data['product_id'])
                vals.append(product_data)
            return vals
        else:
            return super(Inventory, self)._get_inventory_lines_values()

    @api.one
    @api.constrains('filter', 'product_id', 'lot_id', 'partner_id', 'package_id')
    def _check_filter_product(self):
        if self.filter == 'percent' and not (0 < self.percent_number <= 100):
            raise UserError('Error, porcentaje tiene que ser entre 1% y 100%')
        return super(Inventory, self)._check_filter_product()

class l10n_cu_stock_inventory_line(models.Model):
    _inherit = 'stock.inventory.line'

    surplus_physical_quantity = fields.Float('Surplus Physical Quantity',
                                             digits=dp.get_precision('Product Unit of Measure'),
                                             compute='_calculate_surplus')

    import_physical_count = fields.Float('Import Product Physical Count',
                                         digits=dp.get_precision('Product Unit of Measure'),
                                         compute='_calculate_physical_import')

    import_theoretical_count = fields.Float('Import Product Theoretical Count',
                                            digits=dp.get_precision('Product Unit of Measure'),
                                            compute='_calculate_theoretical_import')

    import_surplus = fields.Float('Import Surplus', digits=dp.get_precision('Product Unit of Measure'),
                                  compute='_calculate_surplus_import')

    @api.one
    @api.depends('product_qty', 'theoretical_qty')
    def _calculate_surplus(self):
        self.surplus_physical_quantity = self.theoretical_qty - self.product_qty

    @api.one
    @api.depends('product_qty', 'theoretical_qty', 'product_id')
    def _calculate_surplus_import(self):
        self.import_surplus = self.product_id.standard_price * (self.theoretical_qty - self.product_qty)

    @api.one
    @api.depends('product_qty', 'product_id')
    def _calculate_physical_import(self):
        self.import_physical_count = self.product_qty * self.product_id.standard_price

    @api.one
    @api.depends('theoretical_qty', 'product_id')
    def _calculate_theoretical_import(self):
        self.import_theoretical_count = self.theoretical_qty * self.product_id.standard_price

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        res = super(l10n_cu_stock_inventory_line, self)._get_move_values(qty, location_id, location_dest_id, out)
        res['move_line_ids'][0][2]['warehouse_existing_qty_dest'] = out and 0.0 or self.product_qty
        res['move_line_ids'][0][2]['warehouse_existing_qty'] = out and self.product_qty or 0.0
        return res

