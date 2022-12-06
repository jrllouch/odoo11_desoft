# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import odoo.tools.float_utils as fu


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def _selected_days(self):
        res_setting = self.env['res.config.settings'].search([
        ])
        pos = len(res_setting)
        if pos == 0:
            return 15
        else:
            return res_setting[pos - 1].default_low_move_day

    def _selected_movement_types(self):
        res_setting = self.env['res.config.settings'].search([
        ])
        pos = len(res_setting)
        if pos != 0:
            return res_setting[pos - 1].default_not_use_movement_type

    default_low_move_day = fields.Integer(string='Number of Days',
                                          help="Number of days used in the filter Low Move.",
                                          default=_selected_days, required=True)
    default_not_use_movement_type = fields.Many2many('stock.picking.type', string='Not use this movement type',
                                                     help="Not used this movement type",
                                                     default=_selected_movement_types)
    module_l10n_cu_dualcurrency_stock_account = fields.Boolean("Dual currency management", help="By checking this "
                                                               "option, the l10n_cu_dualcurrency_stock account module "
                                                               "will be installed")
    inventory_lock_date = fields.Date(string="Lock Date", related="company_id.inventory_lock_date", readonly=True,
                                      help="Can't edit documents prior or equal to this date.")

    def set_inventory_lock_date_wizard(self):
        view = self.env.ref('l10n_cu_stock_account.inventory_lock_date_form')
        if self.inventory_lock_date:
            context = {'default_inventory_lock_date': self.inventory_lock_date}
        else:
            context = self.env.context
        return {
            'name': _('Inventory Lock Date'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'inventory.lock.date.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context
        }

    def _selected_products(self):
        res_setting = self.env['res.config.settings'].search([
        ])
        pos = len(res_setting)
        if pos != 0:
            return res_setting[pos - 1].default_not_use_product

    default_not_use_product = fields.Many2many('product.product', string= 'Not use this product',
                                               default=_selected_products)

    def _selected_warehouse(self):
        res_setting = self.env['res.config.settings'].search([
        ])
        pos = len(res_setting)
        if pos != 0:
            return res_setting[pos - 1].default_not_used_warehouse

    default_not_used_warehouse = fields.Many2many('stock.location', string = 'Not use this warehouse',
                                                  default=_selected_warehouse)

    attachment = fields.Many2many('ir.attachment', string='Attachment', ondelete='cascade')
