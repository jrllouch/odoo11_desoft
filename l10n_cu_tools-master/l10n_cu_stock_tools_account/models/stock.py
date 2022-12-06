from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_post(self):
        res = super(StockPicking, self).button_post()
        if self.location_dest_id.is_tools_location or self.location_id.is_tools_location:
            picking = self.env['tools.picking'].search([('custodian_dest_id', '=', self.custodian_dest_id.id),
                                                        ('state', 'in', ['confirmed']),
                                                        ('date', '=', self.date)])
            if picking:
                picking.button_validate()
            return res
        else:
            return res
