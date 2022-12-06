# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, models, api


class AssetConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # @api.multi
    # def _get_account_purchase(self):
    #     company = self.env.user.company_id
    #     if company.account_purchase_id:
    #         return company.account_purchase_id.id
    #     return False
    #
    # @api.multi
    # def _get_account_investments(self):
    #     company = self.env.user.company_id
    #     if company.account_investments_id:
    #         return company.account_investments_id.id
    #     return False
    #
    # @api.multi
    # def _get_adjustment_missing(self):
    #     company = self.env.user.company_id
    #     if company.account_adjustment_missing_id:
    #         return company.account_adjustment_missing_id.id
    #     return False
    #
    # @api.multi
    # def _get_adjustment_loss(self):
    #     company = self.env.user.company_id
    #     if company.account_adjustment_loss_id:
    #         return company.account_adjustment_loss_id.id
    #     return False
    #
    # @api.multi
    # def _get_adjustment_surplus(self):
    #     company = self.env.user.company_id
    #     if company.account_adjustment_surplus_id:
    #         return company.account_adjustment_surplus_id.id
    #     return False
    #
    # @api.multi
    # def _get_asset_journal(self):
    #     company = self.env.user.company_id
    #     if company.asset_journal_id:
    #         return company.asset_journal_id.id
    #     return False

    company_id = fields.Many2one('res.company', 'Company', readonly=True,
                                 default=lambda s: s.env.user.company_id.id)
    account_purchase_id = fields.Many2one('account.account', 'Purchase Account', related='company_id.account_purchase_id')
    account_investments_id = fields.Many2one('account.account', 'Investment Account', related='company_id.account_investments_id')
    account_adjustment_missing_id = fields.Many2one('account.account', 'Missing Adjustment Account', related='company_id.account_adjustment_missing_id')
    account_adjustment_loss_id = fields.Many2one('account.account', 'Loss Adjustment Account', related='company_id.account_adjustment_loss_id')
    account_adjustment_surplus_id = fields.Many2one('account.account', 'Surplus Adjustment Account', related='company_id.account_adjustment_surplus_id')
    asset_journal_id = fields.Many2one('account.journal', 'Asset Journal', related='company_id.asset_journal_id')
    # module_l10n_cu_asset_inventory = fields.Boolean('Installs the module asset inventory',
    #                                            help="This installs the module l10n_cu_asset_inventory.")
    asset_lock_date = fields.Date(string='Lock Date for All Users', related='company_id.asset_lock_date', readonly=True)

    @api.multi
    def set_accounts(self):
        self.ensure_one()
        values = {}
        if self.account_purchase_id:
            values.update({'account_purchase_id': self.account_purchase_id.id})
        if self.account_investments_id:
            values.update({'account_investments_id': self.account_investments_id.id})
        if self.account_adjustment_missing_id:
            values.update({'account_adjustment_missing_id': self.account_adjustment_missing_id.id})
        if self.account_adjustment_loss_id:
            values.update({'account_adjustment_loss_id': self.account_adjustment_loss_id.id})
        if self.account_adjustment_surplus_id:
            values.update({'account_adjustment_surplus_id': self.account_adjustment_surplus_id.id})
        if self.asset_journal_id:
            values.update({'asset_journal_id': self.asset_journal_id.id})
        return self.company_id.write(values)

    @api.multi
    def execute_lock(self):
        data_obj = self.env['ir.model.data']
        compose_form_id = data_obj.get_object_reference('l10n_cu_account_asset', 'account_close_form_view')[1]
        close_type = 'initial_load'
        if self.asset_lock_date:
            close_type = 'period_lock'
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(compose_form_id, 'form')],
            'res_model': 'l10n_cu.account.close',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_close_type': close_type,
                        'default_module_id': self.env.ref('base.module_account_asset').id,
                        'title':  'Asset',
                        }
        }