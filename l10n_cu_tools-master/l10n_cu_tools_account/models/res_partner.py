# -*- coding: utf-8 -*-

# Part of Desoft. See LICENSE file for full copyright and licensing details.

# List of contributors:
# Bernardo Justiz González bernardo.justiz@cmw.desoft.cu

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_account_tools_income_transfer_id = fields.Many2one('account.account', company_dependent=True,
                                                                string="Tools income transfer Account",
                                                                domain="[('deprecated', '=', False)]",
                                                                help="This account will be used instead of the default "
                                                                     "one as the income transfer account for the "
                                                                     "current partner")
    property_account_tools_outgoing_transfer_id = fields.Many2one('account.account', company_dependent=True,
                                                                  string="Tools outgoing transfer Account",
                                                                  domain="[('deprecated', '=', False)]",
                                                                  help="This account will be used instead of the "
                                                                       "default one as the outgoing transfer account "
                                                                       "for the current partner")
