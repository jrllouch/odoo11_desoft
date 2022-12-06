# -*- coding: utf-8 -*-

# Part of Desoft. See LICENSE file for full copyright and licensing details.

# List of contributors:
# Bernardo Justiz González bernardo.justiz@cmw.desoft.cu

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ToolsPicking(models.Model):
    _name = 'tools.picking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Tools Picking"
    _order = 'date desc, id desc'

    name = fields.Char('Reference', default='/', copy=False, index=True, track_visibility='onchange',
                       states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    origin = fields.Char('Source Document', index=True, track_visibility='onchange',
                         states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                         help="Reference of the document")
    note = fields.Text('Notes', track_visibility='onchange')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),
                             ('done', 'Done'),
                             ('cancel', 'Cancelled')], string='Status', default='draft',
                             copy=False, index=True, readonly=True, store=True, track_visibility='onchange',
                             help=" * Draft: not confirmed yet and will not be scheduled until confirmed.\n"
                             " * Waiting Another Operation: waiting for another move to proceed /"
                             "before it becomes automatically available (e.g. in Make-To-Order flows).\n"
                             " * Waiting: if it is not ready to be sent because the required products/"
                             " could not be reserved.\n"
                             " * Ready: products are reserved and ready to be sent. If the shipping policy/"
                             " is 'As soon as possible' this happens as soon as anything is reserved.\n"
                             " * Pending For Accounting: has been processed and pending for accounting.\n"
                             " * Done: has been processed, can't be modified or cancelled anymore.\n"
                             " * Cancelled: has been cancelled, can't be confirmed anymore.")
    custodian_orig_id = fields.Many2one(
        'tools.custodian',
        track_visibility='onchange'
        )
    custodian_dest_id = fields.Many2one(
        'tools.custodian',
        track_visibility='onchange'
        )
    partner_id = fields.Many2one('res.partner', 'Contact')
    date = fields.Datetime('Creation Date', default=fields.Datetime.now, index=True, track_visibility='onchange',
                           states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                           help="Creation Date, usually the time of the order")
    move_lines = fields.One2many('tools.move', 'picking_id', string="Tolls Moves", copy=True)
    picking_type_id = fields.Many2one('tools.picking.type', 'Operation Type',
                                      required=True,
                                      states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    picking_type_code = fields.Selection(related='picking_type_id.code', readonly=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('tools.picking'),
                                 index=True, required=True,
                                 states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    @api.onchange('picking_type_id')
    def on_change_picking_type(self):
        self.custodian_dest_id = False
        self.custodian_orig_id = False


    @api.multi
    def quant_outgoing_update(self, move):
        quant = self.env['tools.quant'].search([('product_id', '=', move.product_id.id), (
            'custodian_id', '=', self.custodian_orig_id.id)], limit=1).sorted(key=lambda r: r.in_date)
        if quant.exists():
            quant.quantity -= move.product_qty
            if quant.quantity == 0:
                quant.unlink()
        else:
            raise UserError(_(
                'No hay existencias de ese útil para el custodio de origen'))

    @api.multi
    def quant_income_update(self, move):
        quant = self.env['tools.quant'].search([('product_id', '=', move.product_id.id),
                                                ('custodian_id', '=', self.custodian_dest_id.id),
                                                ('price', '=', move.price_unit)])
        if quant.exists():
            quant.quantity += move.product_qty
        else:
            vals = {
                'product_id': move.product_id.id,
                'product_tmpl_id': move.product_tmpl_id.id,
                'product_uom_id': move.product_tmpl_id.uom_id.id,
                'company_id': move.company_id.id,
                'custodian_id': self.custodian_dest_id.id,
                'quantity': move.product_qty,
                'price': move.price_unit,
                'in_date': move.date,
            }
            self.env['tools.quant'].create(vals)

    def _is_in(self):
        """ Check if the picking should be considered as entering the company so that the cost method
        will be able to apply the correct logic.

        :return: True if the picking is entering the company else False
        """
        if self.picking_type_code in ('income', 'income_surplus', 'income_transfer'):
            return True
        return False

    def _is_out(self):
        """ Check if the picking should be considered as leaving the company so that the cost method
        will be able to apply the correct logic.

        :return: True if the picking is leaving the company else False
        """
        if self.picking_type_code in ('outgoing', 'outgoing_Missing', 'outgoing_transfer'):
            return True
        return False

    @api.multi
    def _check_state(self):
        for picking in self:
            if picking.state != 'draft':
                raise UserError(
                    _('You cannot delete an picking in a state different to draft.'))

    @api.multi
    def unlink(self):
        self._check_state()
        return super(ToolsPicking, self).unlink()

    @api.multi
    def action_confirm(self):
        if self.move_lines:
            self.move_lines.write({'date': self.date,
                                   'custodian_orig_id': self.custodian_orig_id.id or None,
                                   'custodian_dest_id': self.custodian_dest_id.id or None,
                                   'origin': self.origin or None,
                                   'note': self.note or None,
                                   })
            for move in self.move_lines:
                if move.product_qty == 0:
                    raise UserError(_(
                        'No puede procesar utiles con cantidades en 0'))
                move.state = 'confirmed'
                move.price_unit = move._get_price_unit()
                if self._is_in():
                    self.quant_income_update(move)
                elif self._is_out():
                    self.quant_outgoing_update(move)
                else:
                    self.quant_outgoing_update(move)
                    self.quant_income_update(move)
        else:
            raise UserError(_(
                'No puede confirmar el documento sin utiles que procesar'))
        self.name = self.env['tools.picking.type'].browse(self.picking_type_id.id). \
            sequence_id.next_by_id()
        if self.move_lines:
            self.move_lines.write({'name': self.name
                                   })
        self.state = 'confirmed'
        return True

    @api.multi
    def button_validate(self):
        self.action_confirm()
        for move in self.move_lines:
            move.state = 'done'
        self.state = 'done'
        return True
