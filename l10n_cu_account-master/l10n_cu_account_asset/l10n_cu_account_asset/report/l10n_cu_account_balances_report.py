# -*- coding: utf-8 -*-
'''
    This file contains the code to print the "Account Balances" Report
'''
import time

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import odoo.tools.float_utils as fu
import odoo.addons.decimal_precision as dp


class l10n_cu_account_balances_report(models.AbstractModel):
    '''
    This is the class who obtains and process the necessary
    data to show in the report document.
    '''
    _name = 'report.l10n_cu_account_asset.l10n_cu_account_balances_report'

    def get_report_values(self, docids, data=None):
        '''
        Function _account_category:This method loops through all categories of assets and stored in a data dictionary accounts who are configured.
        @param self:the self object of class Python
        @return: Account data that are configured.
                type: dictionary
        '''

        line_ids = []
        asset_obj = self.env['account.asset.asset']
        company_id = self.env.user.company_id
        assets = asset_obj.search([('company_id', '=', company_id.id),
                                   ('state', 'in', ('open', 'stop', 'idler')),
                                   ('type', 'not in', ('module', 'functional'))])
        if assets:
            account_balance = {}
            mount_precision = self.env['decimal.precision'].precision_get('Account')
            for asset in assets:
                asset_account = asset.category_id.account_asset_id.id
                asset_depreciation_account = asset.category_id.account_depreciation_id.id
                if not asset_account:
                    raise UserError(_("Asset (%s) has no asset account configure. Define an asset account for its category (%s).") % (
                        asset.name, asset.category_id.name))
                elif not asset_depreciation_account:
                    raise UserError(_("Asset (%s) has no depreciation account configure. Define an depreciation account for its category (%s).") % (
                        asset.name, asset.category_id.name))
                else:
                    if asset_account in account_balance:
                        account_balance[asset_account] = account_balance[asset_account] + asset.value
                    else:
                        account_balance[asset_account] = asset.value
                    # if asset.value_amount_depreciation > 0:
                    if asset_depreciation_account in account_balance:
                        account_balance[asset_depreciation_account] = account_balance[asset_depreciation_account] + \
                                                                      asset.value_amount_depreciation
                    else:
                        account_balance[asset_depreciation_account] = asset.value_amount_depreciation
            precision_digits = self.env['decimal.precision'].precision_get(
                'Account')
            for account_id, amount in account_balance.items():
                account = self.env['account.account'].browse(account_id)
                balance = self.env['report.account.report_trialbalance']._get_accounts(account, 'all')[0]['balance']
                dif = fu.float_round(
                    abs(abs(balance) - round(amount, mount_precision)), precision_digits)
                line_ids.append({
                    'account': account.code + ' ' + account.name,
                    'asset_balance': amount,
                    'account_balance': abs(balance), 'difference': dif})
        return {
            'accounts': line_ids
        }
