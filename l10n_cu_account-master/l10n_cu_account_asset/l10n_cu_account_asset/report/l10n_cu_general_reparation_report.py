# -*- coding: utf-8 -*-
'''
    This file contains the code to print the "General Reparation" Report
'''
import time

from odoo import models, fields, api


class l10n_cu_general_reparation_report(models.AbstractModel):
    '''
    This is the class who obtains and process the necessary
    data to show in the report document.
    '''
    _name = 'report.l10n_cu_account_asset.l10n_cu_general_reparation_report'

    def get_report_values(self, docids, data=None):
        '''
        Function _get_assets:Returns a list of assets that have suffered overall repair.
        @param wizobj:the form arguments from Wizard like area of responsibility,
                    filter and others.
                    type: dictionary
                    default value: False
        @return:List of account.asset.asset objects.
                type:list
        '''

        asset_pool = self.env['account.asset.asset']
        company_id = self.env.user.company_id
        end_date = company_id.asset_lock_date

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
                        a.inventory_number, a.name, m.number, m.operation_date, a.value, m.return_date
                        FROM
                        l10n_cu_asset_move m, l10n_cu_asset_move_category mc, account_asset_asset a, asset_move_account_asset_rel rel
                        WHERE
                        m.state = 'terminated' AND m.id = rel.asset_move_id AND rel.asset_id = a.id AND m.asset_move_category_id = mc.id
                        AND mc.code = '11' AND a.id in %s
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
