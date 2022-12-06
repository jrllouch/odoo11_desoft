# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ToolsQuantityHistory(models.TransientModel):
    _name = 'tools.quantity.history'
    _description = 'Tools Quantity History'

    compute_at_date = fields.Selection([
        (0, 'Current Inventory'),
        (1, 'At a Specific Date')
    ], string="Compute", help="Choose to analyze the current inventory or from a specific date in the past.")
    date = fields.Datetime('Inventory at Date', help="Choose a date to get the inventory at that date", default=fields.Datetime.now)

    def open_table(self):
        self.ensure_one()

        if self.compute_at_date:
            tree_view_id = self.env.ref('l10n_cu_tools.view_tools_product_tree').id
            form_view_id = self.env.ref('l10n_cu_tools.tools_product_form_view_procurement_button').id
            # We pass `to_date` in the context so that `qty_available` will be computed across
            # moves until date.
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Products'),
                'res_model': 'product.product',
                'context': dict(self.env.context, to_date=self.date, search_default_category=True),
            }
            return action
        else:
            return self.env.ref('l10n_cu_tools.toolsquantsact').read()[0]
