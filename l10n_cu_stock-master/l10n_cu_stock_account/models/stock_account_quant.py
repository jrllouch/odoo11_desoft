# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from psycopg2 import OperationalError

from odoo import api, fields, models,_
from dateutil.relativedelta import relativedelta
from datetime import timedelta, datetime


class l10n_cu_stock_quant(models.Model):
    _name = 'stock.quant'
    _inherit = 'stock.quant'

    last_date = fields.Datetime('Last Date', readonly=True)
    percent_save_point = fields.Integer(help='Mark inventory percent status', default=0)
    value = fields.Float('Value')

    def custom_date(self):
        low_move_days = 0
        res_setting = self.env['res.config.settings'].search([
        ])
        pos = len(res_setting)
        if pos != 0:
            low_move_days += res_setting[pos - 1].default_low_move_day

        today = fields.Datetime.from_string(fields.Datetime.now())
        date_to_compare = today - relativedelta(days=low_move_days)
        tree_id = self.env.ref("stock.view_stock_quant_tree")
        form_id = self.env.ref("stock.view_stock_quant_form")
        return {
            'type': 'ir.actions.act_window',
            'name': _('Product low movement'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.quant',
            'domain': [('last_date', '<=', date_to_compare)],
            'views': [(tree_id.id, 'tree'), (form_id.id, 'form')],
            'target': 'current',
            'context': {'search_default_internal_loc': 1, 'search_default_stockable': 1,
                        'group_by': ['product_id', 'location_id']}

        }

    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None,
                                   in_date=None, last_date=None, movement_type=None):
        res = super(l10n_cu_stock_quant, self)._update_available_quantity(product_id, location_id, quantity, lot_id,
                                                                          package_id, owner_id, in_date)

        not_ids = []
        not_products = []
        not_warehouse = []
        self = self.sudo()
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                              strict=True)

        res_setting = self.env['res.config.settings'].search([
        ])

        pos = len(res_setting)
        if pos != 0:
            for setting in res_setting[pos - 1]:
                for ids in setting.default_not_use_movement_type:
                    not_ids.append(ids.id)
                for product in setting.default_not_use_product:
                    not_products.append(product.id)
                for warehouse in setting.default_not_used_warehouse:
                    not_warehouse.append(warehouse.id)

        if not_ids.__contains__(movement_type) or not_products.__contains__(product_id.id) or not_warehouse.__contains__(location_id.id):
            for quant in quants:
                try:
                    with self._cr.savepoint():
                        self._cr.execute("SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT", [quant.id],
                                         log_exceptions=False)
                        quant.write({
                            'last_date': "",
                        })
                        break
                except OperationalError as e:
                    if e.pgcode == '55P03':  # could not obtain the lock
                        continue
                    else:
                        raise
        else:
            for quant in quants:
                try:
                    with self._cr.savepoint():
                        self._cr.execute("SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT", [quant.id],
                                         log_exceptions=False)
                        quant.write({
                            'last_date': last_date,
                        })
                        break
                except OperationalError as e:
                    if e.pgcode == '55P03':  # could not obtain the lock
                        continue
                    else:
                        raise
        return res

