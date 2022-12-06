# -*- coding: utf-8 -*-
# Part of DESOFT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import time
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.depends('asset_lock_date')
    def _get_asset_opening_done(self):
        for company in self:
            company.asset_opening_done = company.asset_lock_date != False

    account_purchase_id = fields.Many2one(
        'account.account', 'Purchase Account')
    account_investments_id = fields.Many2one(
        'account.account', 'Investment Account')
    account_adjustment_missing_id = fields.Many2one(
        'account.account', 'Missing Adjustment Account')
    account_adjustment_loss_id = fields.Many2one(
        'account.account', 'Loss Adjustment Account')
    account_adjustment_surplus_id = fields.Many2one(
        'account.account', 'Surplus Adjustment Account')
    asset_journal_id = fields.Many2one('account.journal', 'Asset Journal')
    asset_opening_done = fields.Boolean(
        'Asset Opening Done', compute='_get_asset_opening_done', store=True)
    asset_lock_date = fields.Date(string='Lock Date for All Users')

    @api.constrains('asset_lock_date')
    def _constrains_asset_lock_date(self):
        depreciation_line_ids = self.env['account.asset.depreciation.line'].search([('depreciation_date', '<=', self.asset_lock_date),
                                                                                    ('state', '!=', 'posted')])

        move_line_ids = self.env['l10n_cu.asset.move'].search([('operation_date', '<=', self.asset_lock_date),
                                                               ('state', 'not in', ('draft', 'confirmed'))])
        if depreciation_line_ids:
            raise UserError(
                _('Every depreciation line with depreciation date before the asset lock date (%s) must be posted') % self.asset_lock_date)

        if move_line_ids:
            raise UserError(
                _('Every asset move with operation date before the asset lock date (%s) must be terminated or cancelled') % self.asset_lock_date)

    @api.multi
    def _check_lock_dates(self, vals):
        res = super(ResCompany, self)._check_lock_dates(vals)
        for company in self:
            if company.asset_lock_date and vals.get('period_lock_date', False):
                period_lock_date = vals.get('period_lock_date') and \
                    time.strptime(vals['period_lock_date'],
                                  DEFAULT_SERVER_DATE_FORMAT)
                asset_lock_date = company.asset_lock_date and \
                    time.strptime(company.asset_lock_date,
                                  DEFAULT_SERVER_DATE_FORMAT)

                if asset_lock_date < period_lock_date:
                    raise ValidationError(_('The asset lock date must be equal or greater than the period '
                                            'closing date: %s') % vals['period_lock_date'])
        return res

    @api.model
    def create(self, vals):
        result = super(ResCompany, self).create(vals)
        self.env['account.asset.category']._create_account_asset_category(result)
        return result
