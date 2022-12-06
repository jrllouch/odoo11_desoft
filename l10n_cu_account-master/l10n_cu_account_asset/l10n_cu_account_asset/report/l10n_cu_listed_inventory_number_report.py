# -*- coding: utf-8 -*-
'''
    This file contains the code to print the "Listed Inventory Number" Report
'''
import time

from odoo import models, fields, api


class l10n_cu_listed_inventory_number_report(models.AbstractModel):
    '''
    This is the class who obtains and process the necessary
    data to show in the report document.
    '''
    _name = 'report.l10n_cu_account_asset.l10n_cu_listed_inventory_number_report'
    _table = 'l10n_cu_listed_inventory_number_report'

    @api.model
    def get_report_values(self, docids, data=None):
        '''
        Function _get_assets:Returns with asset data a dictionary as a list of id
        @param wizobj:the form arguments from Wizard like area of responsibility,
                    filter and others.
                    type: dictionary
                    default value: False
        @return:
                type:dict
        '''

        asset_pool = self.env['account.asset.asset']
        company_id = self.env.user.company_id

        domain_asset = [('company_id', '=', company_id.id),
                        ('parent_id', '=', False)]
        area = data['form']['area']
        category_id = data['form']['category_id']
        asset_report = data['form']['asset_report']
        asset_module_report = data['form']['asset_module_report']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']

        if area:
            domain_asset.append(('area', '=', area))

        if category_id:
            domain_asset.append(('category_id', '=', category_id))

        if asset_report:
            domain_asset.append(('id', '=', asset_report))

        if asset_module_report:
            domain_asset.append(('id', '=', asset_module_report))

        if start_date:
            domain_asset.append(('subscribe_date', '>=', start_date))

        if end_date:
            domain_asset.append(('subscribe_date', '<=', end_date))

        asset_ids = asset_pool.search(domain_asset).ids

        result = []
        if asset_ids:
            self.env.cr.execute('''
            SELECT
              a.name, a.inventory_number, a.category_id, a.value, a.subscribe_date, c.name as category, a.unsubscribe_date
              FROM
              account_asset_asset a, account_asset_category c
              WHERE
              a.id in %s AND c.id = a.category_id
              ORDER BY
              a.inventory_number''', (tuple(asset_ids),))

            result = self.env.cr.dictfetchall()
        
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'data': data['form'],
            'assets': result
        }