# -*- coding: utf-8 -*-
'''
    This file contains the code to print the "Asset transfer" Report
'''
import time

from odoo import models, fields, api


class l10n_cu_rented_assets_report(models.AbstractModel):
    '''
    This is the class who obtains and process the necessary
    data to show in the report document.
    '''
    _name = 'report.l10n_cu_account_asset.l10n_cu_rented_assets_report'

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
            # self.localcontext.update({
            #     'area': wizobj['form']['area'][1],
            # })
            domain_asset.append(('area', '=', area))

        if category_id:
            # self.localcontext.update({
            #     'category': wizobj['form']['category_id'][1],
            # })
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

        move_ids = []
        # if wizobj['form']['period_start'] and wizobj['form']['period_end']:
        #     account_period = self.pool.get('account.period')
        #     period_id = wizobj['form']['period_start'][0]
        #     start = account_period.browse(self.cr, self.uid, period_id)[0].date_start
        #     period_id = wizobj['form']['period_end'][0]
        #     end = account_period.browse(self.cr, self.uid, period_id)[0].date_stop

        #     self.localcontext.update({
        #         'period_start': wizobj['form']['period_start'][1],
        #         'period_end': wizobj['form']['period_end'][1]
        #     })
        #     move_obj = self.pool.get('l10n_cu.asset.move')
        #     move_ids = move_obj.search(self.cr, self.uid, [('operation_date', '>=', start),
        #                                                    ('operation_date', '<=', end)])
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        move_ids = self.env['l10n_cu.asset.move'].search([('operation_date', '>=', start_date),
                                                          ('operation_date', '<=', end_date)]).ids

        asset_ids = asset_pool.search(domain_asset).ids
        result = []

        if asset_ids:
            query = '''
                    SELECT
                    a.inventory_number, a.name, m.operation_date, ar.name as area, m.number, m.return_date
                    FROM
                    l10n_cu_asset_move m, l10n_cu_resp_area ar, account_asset_asset a, asset_move_account_asset_rel rel
                    WHERE
                    a.area = ar.id AND m.state = 'terminated' AND m.id = rel.asset_move_id AND rel.asset_id = a.id AND m.asset_move_category_code = '10'
                    AND a.id in %s
                    ORDER BY
                    a.inventory_number'''
            if move_ids:
                query = query.partition('ORDER')[0]
                query += 'AND m.id in %s ORDER BY a.inventory_number'
                self.env.cr.execute(query, (tuple(asset_ids), tuple(move_ids),))
            else:
                self.env.cr.execute(query, (tuple(asset_ids), ))

            result = self.env.cr.dictfetchall()

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'data': data['form'],
            'assets': result
        }
