# -*- coding: utf-8 -*-
'''
    This file contains the code to print the "Account Balances-Subaccount" Report
'''
import time

from odoo import models, fields, api


class l10n_cu_account_subaccount_balances_report(models.AbstractModel):
    '''
    This is the class who obtains and process the necessary
    data to show in the report document.
    '''
    _name = 'report.l10n_cu_account_asset.l10n_cu_account_subaccount_balances_report'
    _table = 'l10n_cu_account_subaccount_balances_report'

    def get_report_values(self, docids, data=None):
        '''
        Function _account_category:This method loops through all categories of assets and stored in a data dictionary accounts who are configured.
        @param self:the self object of class Python
        @return: Account data that are configured.
                type: dictionary
        '''

        category_ids = self.env['account.asset.category']
        result = []
        company_id = self.env.user.company_id
        for category in category_ids:
            flag = False
            if category.asset_ids:
                for asset in category.asset_ids:
                    if asset.state not in ('draft', 'close'):
                        flag = True
                        break
                if flag:
                    report_obj = self.env['report.account.report_trialbalance']

                    if category.account_asset_id:
                        if category.account_asset_id.company_id.id == company_id.id:

                            res = {
                                'id': category.account_asset_id.id,
                                'type': category.account_asset_id.type,
                                'a_code': category.account_asset_id.code,
                                'name': category.account_asset_id.name,
                                'level': category.account_asset_id.level,
                                'debit': category.account_asset_id.debit,
                                'credit': category.account_asset_id.credit,
                                'balance': report_obj._get_accounts(category.account_asset_id, 'all')[0]['balance'],
                                'parent_id': category.account_asset_id.parent_id,
                                'bal_type': '',
                            }
                            if result.count(res) == 0:
                                result.append(res)

                    if category.account_depreciation_id:
                        if category.account_depreciation_id.company_id.id == company_id.id:
                            res = {
                                'id': category.account_depreciation_id.id,
                                'type': category.account_depreciation_id.type,
                                'a_code': category.account_depreciation_id.code,
                                'name': category.account_depreciation_id.name,
                                'level': category.account_depreciation_id.level,
                                'debit': category.account_depreciation_id.debit,
                                'credit': category.account_depreciation_id.credit,
                                'balance': report_obj._get_accounts(category.account_depreciation_id, 'all')[0]['balance'],
                                'parent_id': category.account_depreciation_id.parent_id,
                                'bal_type': '',
                            }
                            if result.count(res) == 0:
                                result.append(res)
        return {
            'accounts': result.sort()
        }
