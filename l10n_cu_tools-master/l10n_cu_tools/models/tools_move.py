# -*- coding: utf-8 -*-

# Part of Desoft. See LICENSE file for full copyright and licensing details.

# List of contributors:
# Bernardo Justiz González bernardo.justiz@cmw.desoft.cu

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class ToolsMove(models.Model):
    _name = 'tools.move'
    _description = "Tools Move"
    _order = 'sequence asc'

    name = fields.Char('Reference', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    sequence = fields.Integer('Sequence', default=10)
    date = fields.Datetime('Creation Date', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                           help="Creation Date, usually the time of the order")
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('tools.move'),
                                 index=True, required=True)
    picking_id = fields.Many2one('tools.picking', 'Transfer Reference', index=True,
                                 states={'done': [('readonly', True)]}, ondelete='cascade')
    custodian_orig_id = fields.Many2one(
        'tools.custodian'
        )
    custodian_dest_id = fields.Many2one(
        'tools.custodian'
        )
    product_id = fields.Many2one('product.product', 'Product', domain=[('type', 'in', ['product', 'consu'])],
                                 index=True, required=True, states={'done': [('readonly', True)]})
    product_tmpl_id = fields.Many2one('product.template', 'Product Template',
                                      related='product_id.product_tmpl_id', help="Technical: used in views")
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True)
    product_uom_qty = fields.Float(
        'Real Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
        default=0.0, required=True, states={'done': [('readonly', True)]},
        help="This is the quantity of products from an inventory "
             "point of view. For moves in the state 'done', this is the "
             "quantity of products that were actually moved.")
    product_qty = fields.Float('Real Quantity', digits=dp.get_precision('Product Unit of Measure'),
                               compute='_compute_product_qty', inverse='_set_product_qty', store=True)
    price_unit = fields.Float('Unit Price',
                              help="Technical field used to record the tools cost set by /"
                                   "the user during a picking confirmation (when costing /"
                                   "method used is 'average price' or 'real'). Value given /"
                                   " in company currency and in product uom.",
                              copy=False)
    state = fields.Selection(
        [('draft', 'New'), ('cancel', 'Cancelled'), ('confirmed', 'Confirmed'), ('done', 'Done')
         ], string='Status',
        copy=False, default='draft', index=True, readonly=True,
        help="* New: When the tools move is created and not yet confirmed.\n"
             "* Waiting Another Move: This state can be seen when a move is waiting  /"
             "for another one, for example in a chained flow.\n"
             "* Waiting Availability: This state is reached when the procurement resolution /"
             "is not straight forward. It may need the scheduler to run, a component to be manufactured...\n"
             "* Available: When products are reserved, it is set to \'Available\'.\n"
             "* Done: When the shipment is processed, the state is \'Done\'.")
    origin = fields.Char('Source Document', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                         help="Reference of the document")
    reference = fields.Char(compute='_compute_reference', string="Reference", store=True)
    note = fields.Text('Notes')
    picking_type_id = fields.Many2one(related='picking_id.picking_type_id')
    inventory_id = fields.Many2one('tools.inventory', 'Inventory')
    picking_code = fields.Selection(related='picking_id.picking_type_id.code')
    product_type = fields.Selection(related='product_id.type')

    def _get_price_unit(self):
        """ Returns the unit price to store on the quant """
        if self.picking_id._is_in():
            return self.product_id.standard_price
        else:
            quant = self.env['tools.quant'].search([('product_id', '=', self.product_id.id), (
                    'custodian_id', '=', self.custodian_orig_id.id)], limit=1).\
                    sorted(key=lambda r: r.in_date)
            return quant.price

    @api.depends('picking_id', 'name')
    def _compute_reference(self):
        for move in self:
            move.reference = move.picking_id.name

    @api.onchange('picking_type_id')
    def onchange_picking_type_id(self):
        if self.picking_type_id.code in ('outgoing', 'outgoing_Missing', 'outgoing_transfer', 'internal'):
            quant = self.env['tools.quant'].search([('custodian_id', '=', self.picking_id.custodian_orig_id.id)]). \
                mapped('product_id')
            domain = {'product_id': [('id', 'in', quant.ids)]}
        else:
            product = self.env['product.product'].search([('product_tmpl_id.categ_id.tool_category', '=', True)]).ids
            domain = {'product_id': [('id', 'in', product)]}

        return {'domain': domain}

    @api.onchange('product_id')
    def onchange_product_id(self):
        product = self.product_id
        self.product_uom = product.uom_id.id
        return {'domain': {'product_uom': [('category_id', '=', product.uom_id.category_id.id)]}}

    @api.onchange('product_uom')
    def onchange_product_uom(self):
        if self.product_uom.factor > self.product_id.uom_id.factor:
            return {
                'warning': {
                    'title': "Unsafe unit of measure",
                    'message': _("You are using a unit of measure smaller than the one you are using in "
                                 "order to stock your product. This can lead to rounding problem on reserved quantity! "
                                 "You should use the smaller unit of measure possible in order to valuate your stock or"
                                 "change its rounding precision to a smaller value (example: 0.00001)."),
                }
            }

    @api.onchange('product_id', 'product_qty')
    def onchange_quantity(self):
        if not self.product_id or self.product_qty < 0.0:
            self.product_qty = 0.0

    @api.one
    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_product_qty(self):
        rounding_method = self._context.get('rounding_method', 'UP')
        self.product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id,
                                                              rounding_method=rounding_method)

    def _set_product_qty(self):
        """ The meaning of product_qty field changed lately and is now a functional field computing the quantity
        in the default product UoM. This code has been added to raise an error if a write is made given a value
        for `product_qty`, where the same write should set the `product_uom_qty` field instead, in order to
        detect errors. """
        raise UserError(_(
            'The requested operation cannot be processed because of a programming error setting the `product_qty` '
            'field instead of the `product_uom_qty`.'))

    # # para cancelar un inventario
    def _action_cancel(self):
        if any(move.state == 'done' for move in self):
            raise UserError(_('You cannot cancel a stock move that has been set to \'Done\'.'))
        for move in self:
            if move.state == 'cancel':
                continue
            move._do_unreserve()
            siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
            if move.propagate:
                # only cancel the next move if all my siblings are also cancelled
                if all(state == 'cancel' for state in siblings_states):
                    move.move_dest_ids.filtered(lambda m: m.state != 'done')._action_cancel()
            else:
                if all(state in ('done', 'cancel') for state in siblings_states):
                    move.move_dest_ids.write({'procure_method': 'make_to_stock'})
                    move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
        self.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})
        return True
