# -*- coding: utf-8 -*-
# Part of DESOFT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    inventory_lock_date = fields.Date(string="Lock Date", help="Can't edit documents prior to and inclusive of this "
                                                               "date.")

    @api.one
    @api.constrains('inventory_lock_date')
    def _check_inventory_lock_date(self):
        pick_count = self.env['stock.picking'].search_count([('date', '<=', self.inventory_lock_date),
                                                             ('state', 'not in', ('done', 'cancel'))])
        if pick_count:
            raise ValidationError(_('There are %s stock pickings with same date or earlier than lock date that are '
                                    'in state different from Done or Cancelled.') % pick_count)
        inv_count = self.env['stock.inventory'].search_count([('date', '<=', self.inventory_lock_date),
                                                              ('state', 'not in', ('done', 'cancel'))])
        if inv_count:
            raise ValidationError(_('There are %s stock inventories with same date or earlier than lock date that are '
                                    'in state different from Validated or Cancelled.') % inv_count)
        if self.inventory_lock_date and self.period_lock_date:
            if self.inventory_lock_date < self.period_lock_date:
                raise ValidationError(_('The inventory lock date must be equal or greater than the lock date for '
                                        'non-advisers: %s') % self.period_lock_date)
