# -*- coding: utf-8 -*-
# Part of Desoft. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, registry, _


class ProcurementRule(models.Model):
    """ A rule describe what a procurement should do; produce, buy, move, ... """
    _inherit = 'procurement.rule'

    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=False,
        help="Operation Type determines the way the picking should be shown in the view, reports, ...")
