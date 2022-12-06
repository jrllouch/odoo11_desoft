# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_utils


class Inventory(models.Model):
    _name = "tools.inventory"
    _description = "Tools Inventory"
    _order = "date desc, id desc"

    name = fields.Char(
        'Inventory Reference',
        readonly=True, required=True,
        states={'draft': [('readonly', False)]})
    date = fields.Datetime(
        'Inventory Date',
        readonly=True, required=True,
        default=fields.Datetime.now,
        help="The date that will be used for the stock level check of the products and the validation of the stock move related to this inventory.")
    line_ids = fields.One2many(
        'tools.inventory.line', 'inventory_id', string='Inventories',
        copy=True, readonly=False,
        states={'done': [('readonly', True)]})
    move_ids = fields.One2many(
        'tools.move', 'inventory_id', string='Created Moves',
        states={'done': [('readonly', True)]})
    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'In Progress'),
        ('done', 'Validated')],
                             copy=False, index=True, readonly=True,
                             default='draft')
    company_id = fields.Many2one(
        'res.company', 'Company',
        readonly=True, index=True, required=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('tools.inventory'))

    custodian_id = fields.Many2one(
        'tools.custodian',
        string='Custodian',
        required=True
        )
    product_id = fields.Many2one(
        'product.product', 'Inventoried Product',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Specify Product to focus your inventory on a particular Product.")
    filter = fields.Selection(
        string='Inventory of', selection='_selection_filter',
        required=True,
        default='none',
        help="If you do an entire inventory, you can choose 'All Products' and it will prefill the inventory with the current stock.  If you only do some products  "
             "(e.g. Cycle Counting) you can choose 'Manual Selection of Products' and the system won't propose anything.  You can also let the "
             "system propose for a single product / lot /... ")
    total_qty = fields.Float('Total Quantity', compute='_compute_total_qty')
    category_id = fields.Many2one(
        'product.category', 'Inventoried Category',
        readonly=True, domain="[('tool_category', '=', True)]", states={'draft': [('readonly', False)]},
        help="Specify Product Category to focus your inventory on a particular Category.")
    import_total = fields.Float('Import Total', digits=dp.get_precision('Product Unit of Measure'),
                                compute='_get_total_import')
    percent_number = fields.Integer('Product Percent', default=10)


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

    @api.one
    @api.depends('product_id', 'line_ids.product_qty')
    def _compute_total_qty(self):
        """ For single product inventory, total quantity of the counted """
        if self.product_id:
            self.total_qty = sum(self.mapped('line_ids').mapped('product_qty'))
        else:
            self.total_qty = 0

    @api.multi
    def unlink(self):
        for inventory in self:
            if inventory.state == 'done':
                raise UserError(_('You cannot delete a validated inventory adjustement.'))
        return super(Inventory, self).unlink()

    @api.model
    def _selection_filter(self):
        """ Get the list of filter allowed according to the options checked
        in 'Settings\Warehouse'. """
        res_filter = [
            ('none', _('All products')),
            ('category', _('One product category')),
            ('product', _('One product only')),
            ('partial', _('Select products manually')),
            ('percent', _('By Percent'))]

        return res_filter

    @api.onchange('filter')
    def onchange_filter(self):
        if self.filter != 'category':
            self.category_id = False
        if self.filter != 'product':
            self.product_id = False

    @api.one
    @api.constrains('filter', 'product_id', 'percent_number')
    def _check_filter_product(self):
        if self.filter == 'none' and self.product_id:
            return
        if self.filter == 'percent' and not (0 < self.percent_number <= 100):
            raise UserError('Error, porcentaje tiene que ser entre 1% y 100%')

    def action_reset_product_qty(self):
        self.mapped('line_ids').write({'product_qty': 0})
        return True

    def action_done(self):
        negative = next((line for line in self.mapped('line_ids') if
                         line.product_qty < 0 and line.product_qty != line.theoretical_qty), False)
        if negative:
            raise UserError(_('You cannot set a negative product quantity in an inventory line:\n\t%s - qty: %s') % (
            negative.product_id.name, negative.product_qty))
        Quant = self.env['tools.quant']
        for line in self.line_ids:
            qs = Quant._gather(line.product_id, self.custodian_id, strict=True)
            for q in qs:
                q.percent_save_point += 1
        self.action_check()
        self.write({'state': 'done'})
        self.post_inventory()
        return True

    def post_inventory(self):
        ToolsPicking = self.env['tools.picking']
        ToolsPickingtype = self.env['tools.picking.type']
        if not (ToolsPickingtype.search([('code', '=', 'outgoing_Missing'), ('company_id', '=', self.company_id.id)], limit=1) or ToolsPickingtype.search([('code', '=', 'income_surplus'), ('company_id', '=', self.company_id.id)], limit=1)):
            raise UserError(_('You cannot validate inventory, you need to update the types of operations'))
        for inv in self:
            move_in = inv.mapped('move_ids').filtered(lambda move: move.state == 'draft' and move.custodian_dest_id)
            move_out = inv.mapped('move_ids').filtered(lambda move: move.state == 'draft' and move.custodian_orig_id)
            if move_out:
                res = {
                    'picking_type_id': ToolsPickingtype.search([('code', '=', 'outgoing_Missing'), ('company_id', '=', inv.company_id.id)], limit=1).id,
                    'custodian_orig_id': self.custodian_id.id,
                    'state': 'draft',
                    'origin': inv.name,
                    'date': inv.date,
                    'company_id': inv.company_id.id,
                }
                picking = ToolsPicking.create(res)
                move_out.write({'picking_id': picking.id, 'date': inv.date})
                picking.action_confirm()
                picking.button_validate()
            if move_in:
                res = {
                    'picking_type_id': ToolsPickingtype.search([('code', '=', 'income_surplus'), ('company_id', '=', inv.company_id.id)], limit=1).id,
                    'custodian_dest_id': self.custodian_id.id,
                    'state': 'draft',
                    'origin': inv.name,
                    'date': inv.date,
                    'company_id': inv.company_id.id,
                }
                picking = ToolsPicking.create(res)
                move_in.write({'picking_id': picking.id, 'date': inv.date})
                picking.action_confirm()
                picking.button_validate()


    def action_check(self):
        """ Checks the inventory and computes the tools move to do """
        # tde todo: clean after _generate_moves
        for inventory in self.filtered(lambda x: x.state not in ('done', 'cancel')):
            # first remove the existing tools moves linked to this inventory
            inventory.mapped('move_ids').unlink()
            inventory.line_ids._generate_moves()

    def action_cancel_draft(self):
        self.mapped('move_ids')._action_cancel()
        self.write({
            'line_ids': [(5,)],
            'state': 'draft'
        })

    def action_start(self):
        for inventory in self.filtered(lambda x: x.state not in ('done', 'cancel')):
            vals = {'state': 'confirm', 'date': fields.Datetime.now()}
            if (inventory.filter != 'partial') and not inventory.line_ids:
                vals.update(
                    {'line_ids': [(0, 0, line_values) for line_values in inventory._get_inventory_lines_values()]})
            inventory.write(vals)
        return True

    def action_inventory_line_tree(self):
        action = self.env.ref('l10n_cu_tools.action_inventory_line_tree').read()[0]
        action['context'] = {
            'default_product_id': self.product_id.id,
            'default_inventory_id': self.id,
        }
        return action

    def _get_inventory_lines_values(self):
        domain = ' custodian_id = %s'
        args = (self.custodian_id.id,)

        vals = []
        Product = self.env['product.product']
        # Empty recordset of products available in tools_quants
        quant_products = self.env['product.product']
        # Empty recordset of products to filter
        products_to_filter = self.env['product.product']

        # case 0: Filter on company
        if self.company_id:
            domain += ' AND company_id = %s'
            args += (self.company_id.id,)

        # case 3: Filter on One product
        if self.product_id:
            domain += ' AND product_id = %s'
            args += (self.product_id.id,)
            products_to_filter |= self.product_id
        # case 2 Filter on One product category
        if self.category_id:
            categ_products = Product.search([('categ_id', '=', self.category_id.id)])
            domain += ' AND product_id = ANY (%s)'
            args += (categ_products.ids,)
            products_to_filter |= categ_products
        # case 5: Filter By Percen
        if self.filter == 'percent':
            # Hago el select de todos los quants, para contarlos:
            self.env.cr.execute("""SELECT COUNT(*)
                                          FROM tools_quant
                                          LEFT JOIN product_product
                                          ON product_product.id = tools_quant.product_id
                                          WHERE  %s""" % domain, args)
            q = self.env.cr.dictfetchall()
            limit = round(self.percent_number * q[0]['count'] / 100, 0)
            domain += ' GROUP BY product_id, custodian_id, percent_save_point ORDER BY percent_save_point ASC '
            domain += 'LIMIT %s'
            args += (limit,)
        else:
            domain += ' GROUP BY product_id, custodian_id, percent_save_point ORDER BY percent_save_point ASC '
        # Selecciono los productos
        self.env.cr.execute("""SELECT product_id, sum(quantity) as product_qty, sum(price) as price, custodian_id, percent_save_point
            FROM tools_quant
            LEFT JOIN product_product
            ON product_product.id = tools_quant.product_id
            WHERE %s""" % domain, args)

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


class InventoryLine(models.Model):
    _name = "tools.inventory.line"
    _description = "Inventory Line"
    _order = "product_name ,inventory_id, product_code"

    inventory_id = fields.Many2one(
        'tools.inventory', 'Inventory',
        index=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', 'Owner')
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('type', '=', 'product')],
        index=True, required=True)
    product_name = fields.Char(
        'Product Name', related='product_id.name', store=True, readonly=True)
    product_code = fields.Char(
        'Product Code', related='product_id.default_code', store=True)
    product_uom_id = fields.Many2one(
        'product.uom', 'Product Unit of Measure',
        required=True,
        default=lambda self: self.env.ref('product.product_uom_unit', raise_if_not_found=True))
    product_qty = fields.Float(
        'Checked Quantity',
        digits=dp.get_precision('Product Unit of Measure'), default=0)
    custodian_id = fields.Many2one(
        'tools.custodian',
        related='inventory_id.custodian_id'
        )
    company_id = fields.Many2one(
        'res.company', 'Company', related='inventory_id.company_id',
        index=True, readonly=True, store=True)
    # TDE FIXME: necessary ? -> replace by location_id
    state = fields.Selection(
        'Status', related='inventory_id.state', readonly=True)
    theoretical_qty = fields.Float(
        'Theoretical Quantity', compute='_compute_theoretical_qty',
        digits=dp.get_precision('Product Unit of Measure'), readonly=True, store=True)
    price = fields.Float('Tools Price',
                         help="Cost used for tools valuation in standard price"
                              "Expressed in the default unit of measure of the tools.")

    surplus_physical_quantity = fields.Float('Surplus Physical Quantity',
                                             digits=dp.get_precision('Product Unit of Measure'),
                                             compute='_calculate_difference')

    import_physical_count = fields.Float('Import Product Physical Count',
                                         digits=dp.get_precision('Account'),
                                         compute='_calculate_import')

    import_theoretical_count = fields.Float('Import Product Theoretical Count',
                                            digits=dp.get_precision('Account'),
                                            compute='_calculate_import')

    import_surplus = fields.Float('Import Surplus', digits=dp.get_precision('Account'),
                                  compute='_calculate_import')

    leftover_physical_quantity = fields.Float('Leftover physical quantity',
                                             digits=dp.get_precision('Product Unit of Measure'),
                                             compute='_calculate_difference')

    import_leftover = fields.Float('Import leftover', digits=dp.get_precision('Account'),
                                  compute='_calculate_import')

    @api.one
    @api.depends('product_qty', 'theoretical_qty')
    def _calculate_difference(self):
        self.surplus_physical_quantity = self.product_qty - self.theoretical_qty if (self.product_qty - self.theoretical_qty) > 0 else 0.0
        self.leftover_physical_quantity = self.theoretical_qty - self.product_qty if (self.theoretical_qty - self.product_qty) > 0 else 0.0

    @api.one
    @api.depends('product_qty', 'theoretical_qty', 'product_id')
    def _calculate_import(self):
        self.import_surplus = self.price * (self.product_qty - self.theoretical_qty) if (self.product_qty - self.theoretical_qty)>0 else 0.0
        self.import_physical_count = self.product_qty * self.price
        self.import_theoretical_count = self.theoretical_qty * self.price
        self.import_leftover = self.price * (self.theoretical_qty - self.product_qty) if (self.theoretical_qty - self.product_qty)>0 else 0.0

    @api.one
    @api.depends('product_id', 'product_uom_id', 'company_id')
    def _compute_theoretical_qty(self):
        if not self.product_id:
            self.theoretical_qty = 0
            return
        theoretical_qty = sum([x.quantity for x in self._get_quants()])
        if theoretical_qty and self.product_uom_id and self.product_id.uom_id != self.product_uom_id:
            theoretical_qty = self.product_id.uom_id._compute_quantity(theoretical_qty, self.product_uom_id)
        self.theoretical_qty = theoretical_qty

    @api.onchange('product_id')
    def onchange_product(self):
        res = {}
        # If no UoM or incorrect UoM put default one from product
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
            res['domain'] = {'product_uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        return res

    @api.onchange('product_id', 'product_uom_id')
    def onchange_quantity_context(self):
        if self.product_id and self.product_id.uom_id.category_id == self.product_uom_id.category_id:  # TDE FIXME: last part added because crash
        # if self.product_id and self.product_id.uom_id.category_id == self.product_uom_id.category_id:
            self._compute_theoretical_qty()
            self.product_qty = self.theoretical_qty

    @api.multi
    def write(self, values):
        values.pop('product_name', False)
        res = super(InventoryLine, self).write(values)
        return res

    @api.model
    def create(self, values):
        values.pop('product_name', False)
        if 'product_id' in values and 'product_uom_id' not in values:
            values['product_uom_id'] = self.env['product.product'].browse(values['product_id']).uom_id.id
        existings = self.search([
            ('product_id', '=', values.get('product_id')),
            ('inventory_id.state', '=', 'confirm')
            ])
        res = super(InventoryLine, self).create(values)
        if existings:
            raise UserError(_("You cannot have two inventory adjustements in state 'in Progress' with the same product "
                              "(%s). Please first validate "
                              "the first inventory adjustement with this product before creating another one.") %
                            (res.product_id.display_name))
        return res

    @api.constrains('product_id')
    def _check_product_id(self):
        """ As no quants are created for consumable products, it should not be possible do adjust
        their quantity.
        """
        for line in self:
            if line.product_id.type != 'product':
                raise UserError(_("You can only adjust stockable products.") + '\n\n%s -> %s' % (
                line.product_id.display_name, line.product_id.type))

    def _get_quants(self):
        return self.env['tools.quant'].search([
            ('company_id', '=', self.company_id.id),
            ('product_id', '=', self.product_id.id)
            ])
    # va custodain id
    def _get_move_values(self, qty, out):
        self.ensure_one()
        return {
            'name': _('INV:') + (self.inventory_id.name or ''),
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': qty,
            'date': self.inventory_id.date,
            'company_id': self.inventory_id.company_id.id,
            'inventory_id': self.inventory_id.id,
            'state': 'draft',
            'custodian_orig_id': self.custodian_id.id if out else False,
            'custodian_dest_id': self.custodian_id.id if not out else False,
        }

    def _generate_moves(self):
        moves = self.env['tools.move']
        for line in self:
            if float_utils.float_compare(line.theoretical_qty, line.product_qty,
                                         precision_rounding=line.product_id.uom_id.rounding) == 0:
                continue
            diff = line.theoretical_qty - line.product_qty
            if diff < 0:  # found more than expected
                # vals = line._get_move_values(abs(diff), line.product_id.property_stock_inventory.id, False)
                vals = line._get_move_values(abs(diff),  False)
            else:
                # vals = line._get_move_values(abs(diff),  line.product_id.property_stock_inventory.id, True)
                vals = line._get_move_values(abs(diff),   True)
            moves |= self.env['tools.move'].create(vals)
        return moves
