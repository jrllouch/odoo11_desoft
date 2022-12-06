# -*- coding: utf-8 -*-
'''
    This file contains the code to print the "Lows" Report
'''
import time

from odoo import models, fields, api


class l10n_cu_low_report(models.AbstractModel):
    '''
    This is the class who obtains and process the necessary
    data to show in the report document.
    '''
    _name = 'report.l10n_cu_account_asset.l10n_cu_low_report'

    @api.model
    def get_report_values(self, docids, data=None):
        '''
        Function _get_assets:Returns a data of an asset in an array given an id.
        @param obj:
                    type: dictionary
                    default value: False
        @return:List of account.asset.asset objects.
                type:list
        '''
        asset_pool = self.env['account.asset.asset']
        company_id = self.env.user.company_id

        domain_asset = [('company_id', '=', company_id.id),
                        ('state', '=', 'close'),
                        ('parent_id', '=', False)]

        area = data['form']['area']
        category_id = data['form']['category_id']
        asset_report = data['form']['asset_report']
        asset_module_report = data['form']['asset_module_report']

        if area:
            domain_asset.append(('area', '=', area))

        if category_id:
            domain_asset.append(('category_id', '=', category_id))

        if asset_report:
            # self.localcontext.update({
            #     'asset_report': wizobj['form']['asset_report'][1],
            # })
            domain_asset.append(('id', '=', asset_report))

        if asset_module_report:
            # self.localcontext.update({
            #     'asset_module_report': wizobj['form']['asset_module_report'][1],
            # })
            domain_asset.append(('id', '=', asset_module_report))

        asset_ids = asset_pool.search(domain_asset).ids

        listIds = []
        if asset_ids:
            start_date = data['form']['start_date']
            end_date = data['form']['end_date']
            move_ids = self.env['l10n_cu.asset.move'].search([('operation_date', '>=', start_date),
                                                              ('operation_date', '<=', end_date)]).ids

            if move_ids:
                self.env.cr.execute('''
                    SELECT
                        a.inventory_number, a.name, am.number, a.unsubscribe_date, a.final_value, a.depreciation_tax, a.value_amount_depreciation
                    FROM
                        l10n_cu_asset_move am, l10n_cu_asset_move_category mc, account_asset_asset a, asset_move_account_asset_rel rel
                    WHERE
                        am.state = 'terminated' AND mc.id = am.asset_move_category_id AND mc.code in ('03', '05', '06', '12') AND am.id = rel.asset_move_id AND rel.asset_id = a.id AND a.id in %s AND am.id in %s
                    ORDER BY
                        a.inventory_number ''', (tuple(asset_ids), tuple(move_ids),))
                listIds = self.env.cr.dictfetchall()

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'data': data['form'],
            'assets': listIds
        }
