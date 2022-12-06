# -*- coding: utf-8 -*-
'''
    This file contains the code to print the "Valuation" Report
'''
import time

from odoo import models, fields, api


class l10n_cu_reevaluation_report(models.AbstractModel):
    '''
    This is the class who obtains and process the necessary
    data to show in the report document.
    '''
    _name = 'report.l10n_cu_account_asset.l10n_cu_reevaluation_report'

    @api.model
    def get_report_values(self, docids, data=None):
        '''
        Function _get_assets:Returns a list of assets that has made ​​him a reevaluation.
        @param wizobj:the form arguments from Wizard like area of responsibility,
                    filter and others.
                    type: dictionary
                    default value: False
        @return:List of account.asset.asset objects.
                type:list
        '''

        asset_pool = self.env['account.asset.asset']
        company_id = self.env.user.company_id
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']

        domain_asset = [('company_id', '=', company_id.id),
                        ('state', 'in', ('open', 'idler', 'stop')),
                        ('parent_id', '=', False)]

        area = data['form']['area']
        category_id = data['form']['category_id']
        asset_report = data['form']['asset_report']
        asset_module_report = data['form']['asset_module_report']

        result = {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'data': data['form'],
            'assets': []
        }

        if area:
            domain_asset.append(('area', '=', area))

        if category_id:
            domain_asset.append(('category_id', '=', category_id))

        if asset_report:
            domain_asset.append(('id', '=', asset_report))

        if asset_module_report:
            domain_asset.append(('id', '=', asset_module_report))

        assets = asset_pool.search(domain_asset)

        if assets:
            domain_history = [('asset_id', 'in', assets.ids),
                              ('modification_type', '=', 2)]

            if start_date:
                domain_history.append(('date', '>=', start_date))

            if end_date:
                domain_history.append(('date', '<=', end_date))

            history_ids = self.env['account.asset.history'].search(
                domain_history)

            if history_ids:
                rows = []
                for asset in assets:
                    for history in history_ids:
                        if history.asset_id.id == asset.id:
                            value = {
                                'a_inventory_number': asset.inventory_number,
                                'name': asset.name,
                                'initial_value': history.previous_value,
                                'value': history.value,
                                'date': history.date,
                                'a_id': asset.id,
                            }
                            result['assets'].append(value)
        return result
