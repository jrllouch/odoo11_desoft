# -*- coding: utf-8 -*-
'''
    This file contains the code to print the "Asset transfer" Report
'''
import time

from odoo import models, fields, api


class l10n_cu_assets_transfers_report(models.AbstractModel):
    '''
    This is the class who obtains and process the necessary
    data to show in the report document.
    '''
    _name = 'report.l10n_cu_account_asset.l10n_cu_assets_transfers_report'

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
                        ('state', 'in', ('open', 'idler', 'stop')),
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
            domain_asset.append(('id', '=', asset_report))

        if asset_module_report:
            domain_asset.append(('id', '=', asset_module_report))

        asset_ids = asset_pool.search(domain_asset).ids

        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        move_ids = self.env['l10n_cu.asset.move'].search([('operation_date', '>=', start_date),
                                                          ('operation_date', '<=', end_date)]).ids

        result = []
        if asset_ids:
            query = '''
                    SELECT
                        a.inventory_number, a.name, m.operation_date, m.area as origin_area, ar.name as reception_area, m.number
                        FROM
                        l10n_cu_asset_move m, l10n_cu_asset_move_category mc, account_asset_asset a, l10n_cu_resp_area ar, asset_move_account_asset_rel rel
                        WHERE
                        m.state = 'terminated' AND m.id = rel.asset_move_id AND rel.asset_id = a.id AND m.asset_move_category_id = mc.id
                        AND mc.code = '04' AND a.id in %s AND m.reception_area = ar.id
                        ORDER BY
                        a.inventory_number
                        '''
            if move_ids:
                query = query.partition('ORDER')[0]
                query += 'AND m.id in %s ORDER BY a.inventory_number'
                self.env.cr.execute(query, (tuple(asset_ids), tuple(move_ids),))
            else:
                self.env.cr.execute(query, (tuple(asset_ids),))
            result = self.env.cr.dictfetchall()

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'data': data['form'],
            'assets': result
        }
