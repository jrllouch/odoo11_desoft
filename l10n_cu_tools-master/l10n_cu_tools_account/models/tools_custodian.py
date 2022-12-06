# -*- coding: utf-8 -*-

# Part of Desoft. See LICENSE file for full copyright and licensing details.

# List of contributors:
# Bernardo Justiz González bernardo.justiz@desoft.cu

from odoo import api, fields, models, _


class Custodian(models.Model):
    _inherit = 'tools.custodian'

    expense_account = fields.Many2one('account.account', string='Expense Account',
                                      help="The Expense Account.")
    analytic_account = fields.Many2one('account.analytic.account', string='Analytic Account',
                                       help="The Analytic Account.")

