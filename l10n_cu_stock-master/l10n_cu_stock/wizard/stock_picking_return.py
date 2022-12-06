# -*- coding: utf-8 -*-
# Part of Desoft. See ICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = super(ReturnPicking, self)._prepare_move_default_values(return_line, new_picking)
        vals.update({
            'price_unit': return_line.move_id.price_unit*-1,
        })
        return vals
