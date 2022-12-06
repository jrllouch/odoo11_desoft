# -*- coding: utf-8 -*-

# Part of Desoft. See LICENSE file for full copyright and licensing details.

# List of contributors:
# Bernardo Justiz González bernardo.justiz@cmw.desoft.cu

from odoo import models, fields, api


class ToolsQuant(models.Model):
    _inherit = 'tools.quant'

    value = fields.Float('Tools Value', help="Value used for tools valuation in standard price"
                         "Expressed in the default unit of measure of the tools.")
    amortization = fields.Float('Tools Amortization', help="Amortization used for tools valuation in standard price"
                                "Expressed in the default unit of measure of the tools.")
