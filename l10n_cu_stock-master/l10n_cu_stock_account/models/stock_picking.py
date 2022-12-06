# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare


class PickingType(models.Model):
    _inherit = "stock.picking.type"
    template = fields.Many2one('l10n_cu_stock_account.template', string='Plantilla')
    show_operations = fields.Boolean('Show Detailed Operations', default=True, help="If this checkbox is ticked, the "
                                     "pickings lines will represent detailed stock operations. If not, the picking "
                                     "lines will represent an aggregate of detailed stock operations.")
    operation_between_dependencies = fields.Boolean(string="Operation between dependencies")
    field_domain_dest = fields.Binary('Field Domain Destination', compute='_compute_field_domain_dest')
    field_domain_src = fields.Binary('Field Domain Source', compute='_compute_field_domain_src')

    @api.onchange('code')
    def onchange_picking_code(self):
        self.template = False

    @api.model
    def fill_show_operations(self):
        stock_picking_types = self.env['stock.picking.type'].search(['&', ('show_operations', '=', False), '|',
                                                                     ('active', '=', True), ('active', '=', False)])
        stock_picking_types.write({'show_operations': True})

    @api.multi
    @api.depends('operation_between_dependencies', 'code')
    def _compute_field_domain_src(self):
        domain = []
        for sptype in self:
            if sptype.operation_between_dependencies:
                if sptype.code == 'incoming':
                    domain = [('usage', '=', 'transit')]
            sptype.field_domain_src = domain

    @api.multi
    @api.depends('operation_between_dependencies', 'code')
    def _compute_field_domain_dest(self):
        domain = []
        for sptype in self:
            if sptype.operation_between_dependencies:
                if sptype.code == 'outgoing':
                    domain = [('usage', '=', 'transit')]
            sptype.field_domain_dest = domain


class Picking(models.Model):
    _inherit = "stock.picking"
    _order = "priority desc, date desc, id desc"

    location_id_usage = fields.Boolean(string='Usage', compute='_compute_valor_ori')
    location_dest_id_usage = fields.Boolean(string='Usage1', compute='_compute_valor_des')

    @api.depends('location_id')
    def _compute_valor_ori(self):
        if self.location_id.usage == 'internal':
            self.location_id_usage = True
        else:
            self.location_id_usage = False

    @api.depends('location_dest_id')
    def _compute_valor_des(self):
        if self.location_dest_id.usage == 'internal':
            self.location_dest_id_usage = True
        else:
            self.location_dest_id_usage = False

    name = fields.Char(states={'pending': [('readonly', True)],
                               'done': [('readonly', True)],
                               'cancel': [('readonly', True)]})
    origin = fields.Char(states={'pending': [('readonly', True)],
                                 'done': [('readonly', True)],
                                 'cancel': [('readonly', True)]})
    backorder_id = fields.Many2one(states={'pending': [('readonly', True)],
                                           'done': [('readonly', True)],
                                           'cancel': [('readonly', True)]})
    move_type = fields.Selection(states={'pending': [('readonly', True)],
                                         'done': [('readonly', True)],
                                         'cancel': [('readonly', True)]})
    priority = fields.Selection(states={'pending': [('readonly', True)],
                                        'done': [('readonly', True)],
                                        'cancel': [('readonly', True)]})
    scheduled_date = fields.Datetime(states={'pending': [('readonly', True)],
                                             'done': [('readonly', True)],
                                             'cancel': [('readonly', True)]})
    date = fields.Datetime(states={'pending': [('readonly', True)],
                                   'done': [('readonly', True)],
                                   'cancel': [('readonly', True)]})
    partner_id = fields.Many2one(states={'pending': [('readonly', True)],
                                         'done': [('readonly', True)],
                                         'cancel': [('readonly', True)]})
    company_id = fields.Many2one(states={'pending': [('readonly', True)],
                                         'done': [('readonly', True)],
                                         'cancel': [('readonly', True)]})
    owner_id = fields.Many2one(states={'pending': [('readonly', True)],
                                       'done': [('readonly', True)],
                                       'cancel': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('pending', 'Pending For Accounting'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, track_visibility='onchange',
        help=" * Draft: not confirmed yet and will not be scheduled until confirmed.\n"
             " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows).\n"
             " * Waiting: if it is not ready to be sent because the required products could not be reserved.\n"
             " * Ready: products are reserved and ready to be sent. If the shipping policy is 'As soon as possible' this happens as soon as anything is reserved.\n"
             " * Pending For Accounting: has been processed and pending for accounting.\n"
             " * Done: has been processed, can't be modified or cancelled anymore.\n"
             " * Cancelled: has been cancelled, can't be confirmed anymore.")
    sequence_id = fields.Char('Número consecutivo', readonly=True)
    total_import = fields.Float(compute='_calculate_total_import')
    analytic_account_id = fields.Many2one('account.analytic.account', string=u'Analytic Account',
                                          states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    @api.depends('move_type', 'move_lines.state', 'move_lines.picking_id', 'move_lines.account_move_ids')
    @api.one
    def _compute_state(self):
        if any(move._accounting_pending() for move in self.move_lines):
            self.state = 'pending'
        else:
            super(Picking, self)._compute_state()

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('report.number') or '/'
        vals['sequence_id'] = seq
        return super(Picking, self).create(vals)

    @api.multi
    def _calculate_total_import(self):
        for record in self:
            for move in record.move_lines:
                if move.value:
                    record.total_import += abs(move.value)
                else:
                    record.total_import += move.quantity_done * move.product_id.standard_price

    @api.onchange('analytic_account_id')
    def onchange_analytic_account_id(self):
        for record in self:
            for move in record.move_lines:
                move.write({'analytic_account_id': self.analytic_account_id.id})

    @api.multi
    def button_validate(self):
        count = self.env['stock.picking'].search_count([('state', 'in', ('pending', 'done')), ('date', '>', self.date)])
        if count >= 1:
            raise ValidationError(_("The document can't validate because there are %s documents in state Pending or "
                                    "Done and date greater than the document date.") % (count,))
        value = super(Picking, self).button_validate()
        product_warnings = list()
        for move_line in self.move_line_ids:
            # obteniendo el saldo en existencia

            existing_qty = 0.0
            existing_qty_dest = 0.0
            if move_line.location_id.usage == 'internal':
                location_id = move_line.location_id.id
                quant = self.env['stock.quant'].search(
                    [('product_id.id', '=', move_line.product_id.id),
                     ('location_id.id', '=', location_id)])
                existing_qty = quant.quantity
                if value:
                    existing_qty -= move_line.qty_done

            if move_line.location_dest_id.usage == 'internal':
                location_dest = move_line.location_dest_id.id
                quant_dest = self.env['stock.quant'].search(
                    [('product_id.id', '=', move_line.product_id.id),
                     ('location_id.id', '=', location_dest)])
                existing_qty_dest = quant_dest.quantity
                if value:
                    existing_qty_dest += move_line.qty_done

            # verificando el saldo en existencia contra el campo existencia segun almacen
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(existing_qty, move_line.warehouse_existing_qty, precision_digits=precision_digits) != 0:
                product_warnings.append('No coincide la cantidad según almacén (' + str(move_line.warehouse_existing_qty) +
                                        ') con la cantidad según submayor (' + str(existing_qty) +
                                        ') para ' + move_line.product_id.name + ' en ' + move_line.location_id.complete_name)
            elif float_compare(existing_qty_dest, move_line.warehouse_existing_qty_dest, precision_digits=precision_digits) != 0:
                product_warnings.append('No coincide la cantidad según almacén (' + str(move_line.warehouse_existing_qty_dest) +
                                        ') con la cantidad según submayor (' + str(existing_qty_dest) +
                                        ') para ' + move_line.product_id.name + ' en ' + move_line.location_dest_id.complete_name)

        if len(product_warnings):
            raise UserError('. \n'.join(product_warnings))

        return value

    @api.multi
    def button_post(self):
        for pick in self.filtered(lambda picking: picking.state == 'pending'):
            for move in pick.move_lines.filtered(lambda m: m._accounting_pending()):
                move._run_valuation()
                move.with_context(force_accounting=True)._account_entry_move()

    @api.one
    @api.constrains('date')
    def _check_date(self):
        if self.company_id.inventory_lock_date:
            if self.date[:10] <= self.company_id.inventory_lock_date:
                raise ValidationError(_('The date: %s, must be greater than the inventory lock date: %s')
                                      % (self.date[:10], self.company_id.inventory_lock_date))

    @api.multi
    def action_done(self):
        value = super(Picking, self).action_done()
        for pick in self:
            if pick.picking_type_id.operation_between_dependencies:
                if pick.picking_type_id.code == 'outgoing':
                    if pick.partner_id.company_id:
                        if pick.partner_id.company_id.id != pick.company_id.id:
                            other = self.env['stock.picking.type'].search([('code', '=', 'incoming'),
                                                                           ('operation_between_dependencies', '=', True),
                                                                           ('warehouse_id.company_id.id', '=', pick.partner_id.company_id.id)],
                                                                          limit=1)
                            if other:
                                res = self.env['res.config.settings'].get_values()
                                if res['company_share_product']:
                                    pick_in = self.env['stock.picking'].create({
                                        'partner_id': pick.company_id.partner_id.id,
                                        'origin': pick.name,
                                        'company_id': pick.partner_id.company_id.id,
                                        'picking_type_id': other.id,
                                        'location_id': pick.location_dest_id.id,
                                        'location_dest_id': other.default_location_dest_id.id
                                    })
                                    for sml in pick.move_line_ids:
                                        new_move = self.env['stock.move'].create({
                                            'name': _('New Move:') + sml.product_id.display_name,
                                            'product_id': sml.product_id.id,
                                            'product_uom_qty': sml.qty_done,
                                            'product_uom': sml.product_uom_id.id,
                                            'location_id': pick.location_dest_id.id,
                                            'location_dest_id': other.default_location_dest_id.id,
                                            'picking_id': pick_in.id,
                                            'state': 'partially_available'
                                        })
                                        new_move_line = self.env['stock.move.line'].create({
                                            'product_id': sml.product_id.id,
                                            'product_uom_qty': sml.qty_done,
                                            'product_uom': sml.product_uom_id.id,
                                            'product_uom_id': sml.product_uom_id.id,
                                            'location_id': pick.location_dest_id.id,
                                            'location_dest_id': other.default_location_dest_id.id,
                                            'picking_id': pick_in.id,
                                            'move_id': new_move.id
                                        })
        return True


class Move(models.Model):
    _inherit = "stock.move"

    @api.model
    def _default_analytic_account(self):
        if self._context.get('analytic_account_id'):
            return self._context.get('analytic_account_id')

    analytic_account_id = fields.Many2one('account.analytic.account', string=u'Analytic Account',
                                          default=_default_analytic_account)

    def _account_entry_move(self):
        """ Accounting Valuation Entries """
        if self._context.get('force_accounting', False):
            super(Move, self)._account_entry_move()

    @api.multi
    def _accounting_pending(self):
        self.ensure_one()
        if self.product_id.type != 'product' or self.product_id.valuation != 'real_time':
            # no stock valuation
            return False
        if self.restrict_partner_id:
            # if the move isn't owned by the company, we don't make any valuation
            return False
        return self.state == 'done' and not self.sudo().account_move_ids and \
               (self._is_in() or self._is_out() or self._is_dropshipped())

    # En donde esta funcion.
    # or self._is_dropshipped_returned()

    def _set_analytic_account(self, account_entry_list):
        for account_entry in account_entry_list:
            if account_entry[2]["account_id"] != self.product_id.categ_id.property_stock_valuation_account_id.id:
                update_fields = {
                    'analytic_account_id': self.analytic_account_id.id
                }
                account_entry[2].update(update_fields)
        return account_entry_list

    @api.multi
    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        self.ensure_one()
        if not self._have_location_account() and not self._have_location_account(False):
            res = super(Move, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
            if not self.analytic_account_id:
                return res
            else:
                return self._set_analytic_account(res)

        if self._context.get('forced_ref'):
            ref = self._context['forced_ref']
        else:
            ref = self.picking_id.name

        price = self._get_price_unit()
        for ml in self.move_line_ids:
            dict_accounts = ml._prepare_account_move_line(credit_account_id, debit_account_id)

        partner_id = (self.picking_id.partner_id and self.env['res.partner']._find_accounting_partner(self.picking_id.partner_id).id) or False
        res = []
        for account, qty in dict_accounts.items():
            amount = qty * abs(price)
            line_vals = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': ref,
                'partner_id': partner_id,
                'debit': amount if amount > 0 else 0,
                'credit': -amount if amount < 0 else 0,
                'account_id': account,
            }
            res.append((0, 0, line_vals))

        if not self.analytic_account_id:
            return res
        else:
            return self._set_analytic_account(res)

    def _have_location_account(self, origin=True):
        for ml in self.move_line_ids:
            if origin:
                if not ml.location_id.valuation_out_account_id:
                    return False
            else:
                if not ml.location_dest_id.valuation_in_account_id:
                    return False
        return True

    @api.multi
    def _get_accounting_data_for_valuation(self):
        """ Return the accounts and journal to use to post Journal Entries for
        the real-time valuation of the quant. """
        self.ensure_one()
        accounts_data = self.product_id.product_tmpl_id.get_product_accounts()

        if self.location_id.valuation_out_account_id:
            acc_src = self.location_id.valuation_out_account_id.id
        else:
            acc_src = accounts_data['stock_input'].id

        if self.location_dest_id.valuation_in_account_id:
            acc_dest = self.location_dest_id.valuation_in_account_id.id
        else:
            acc_dest = accounts_data['stock_output'].id

        acc_valuation = accounts_data.get('stock_valuation', False)
        if acc_valuation:
            acc_valuation = acc_valuation.id
        if not accounts_data.get('stock_journal', False):
            raise UserError(_('You don\'t have any stock journal defined on your product category, check if you have '
                              'installed a chart of accounts'))
        if not acc_src and not self._have_location_account():
            raise UserError(_('Cannot find a stock input account for the product %s. You must define one on the product'
                              ' category, or on the location, before processing this operation.') % (self.product_id.display_name))
        if not acc_dest and not self._have_location_account(False):
            raise UserError(_('Cannot find a stock output account for the product %s. You must define one on the '
                              'product category, or on the location, before processing this operation.') % (self.product_id.display_name))
        if not acc_valuation:
            raise UserError(_('You don\'t have any stock valuation account defined on your product category. You must '
                              'define one before processing this operation.'))
        journal_id = accounts_data['stock_journal'].id
        return journal_id, acc_src, acc_dest, acc_valuation


class MoveLine(models.Model):
    _inherit = "stock.move.line"

    warehouse_existing_qty = fields.Float(digits=dp.get_precision('Product Unit of Measure'),
                                          string=u'Existencia Origen', help="Existencia según almacén origen")
    warehouse_existing_qty_dest = fields.Float(digits=dp.get_precision('Product Unit of Measure'),
                                               string=u'Existencia Destino', help="Existencia según almacén destino")

    @api.multi
    def _get_accounting_data_for_valuation(self, credit_account_id, debit_account_id):
        self.ensure_one()
        if not self.owner_id and not self.location_id._should_be_valued() and self.location_dest_id._should_be_valued():
            if self.location_id.usage == 'customer':
                if self.location_dest_id.valuation_in_account_id:
                    credit_account_id = self.location_dest_id.valuation_in_account_id.id
            else:
                if self.location_id.valuation_out_account_id:
                    credit_account_id = self.location_id.valuation_out_account_id.id

        if not self.owner_id and self.location_id._should_be_valued() and not self.location_dest_id._should_be_valued():
            if self.location_dest_id.usage == 'supplier':
                if self.location_id.valuation_out_account_id:
                    debit_account_id = self.location_id.valuation_out_account_id.id
            else:
                if self.location_dest_id.valuation_in_account_id:
                    debit_account_id = self.location_dest_id.valuation_in_account_id.id

        if self.move_id.company_id.anglo_saxon_accounting:
            if self.location_id.usage == 'supplier' and self.location_dest_id.usage == 'customer':
                if self.location_id.valuation_out_account_id:
                    credit_account_id = self.location_id.valuation_out_account_id.id
                if self.location_dest_id.valuation_in_account_id:
                    debit_account_id = self.location_dest_id.valuation_in_account_id.id
            elif self.location_id.usage == 'customer' and self.location_dest_id.usage == 'supplier':
                if self.location_id.valuation_out_account_id:
                    debit_account_id = self.location_id.valuation_out_account_id.id
                if self.location_dest_id.valuation_in_account_id:
                    credit_account_id = self.location_dest_id.valuation_in_account_id.id
        return credit_account_id, debit_account_id

    @api.multi
    def _prepare_account_move_line(self, credit_account_id, debit_account_id):
        self.ensure_one()
        dict = {}
        for move_line in self:
            credit_account_id, debit_account_id = move_line._get_accounting_data_for_valuation(credit_account_id, debit_account_id)
            dict.setdefault(credit_account_id, 0)
            dict[credit_account_id] -= move_line.qty_done
            dict.setdefault(debit_account_id, 0)
            dict[debit_account_id] += move_line.qty_done
        return dict
