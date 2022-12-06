# -*- coding: utf-8 -*-
'''
    This file contains the code to print the "Month Amortization Register" Report
'''
import time
from odoo import models, fields, api


class l10n_cu_month_amortization_report(models.AbstractModel):
    '''
    This is the class who obtains and process the necessary
    data to show in the report document.
    '''
    _name = 'report.l10n_cu_account_asset.l10n_cu_month_amortization_report'
    # def __init__(self, cr, uid, name, context):
    #     '''
    #     Function __init__: Function to be used by rml file to obtain
    #     the document style, static data and basic information to be shown
    #     in PDF document.
    #     '''
    #     super(l10n_cu_month_amortization_report, self).__init__(cr, uid, name, context=context)
    #     self.localcontext.update({
    #         'time': time,
    #         'get_assets':self._get_assets,
    #         })
    #     self.id_obj = {}

    # def _get_assets(self, wizobj):
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
        company_id = self.env.user.company_id.id
        domain_asset = [('company_id', '=', company_id),
                        ('state', 'in', ('open', 'idler', 'stop', 'close')),
                        ('parent_id', '=', False)]
        area = data['form']['area']
        category_id = data['form']['category_id']
        asset_report = data['form']['asset_report']
        asset_module_report = data['form']['asset_module_report']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']

        if area:
            domain_asset.append(('area', '=', data['form']['area'][0]))

        if category_id:
            domain_asset.append(('category_id', '=', data['form']['category_id'][0]))

        if asset_report:
            # self.localcontext.update({
            #     'asset_report': data['form']['asset_report'][1],
            # })
            domain_asset.append(('id', '=', data['form']['asset_report'][0]))

        if asset_module_report:
            # self.localcontext.update({
            #     'asset_module_report': data['form']['asset_module_report'][1],
            # })
            domain_asset.append(('id', '=', data['form']['asset_module_report'][0]))

        asset_ids = asset_pool.search(domain_asset).ids
        listIds = []
        listres = []
        if asset_ids:
            depreciation_asset_pool = self.env['account.asset.depreciation.line']
            domain_depreciation = [('asset_id', 'in', tuple(asset_ids))]
            if start_date:
                domain_depreciation.append(('depreciation_date', '>=', start_date))
            if end_date:
                domain_depreciation.append(('depreciation_date', '<=', end_date))
            # if data['form']['period_start'] and data['form']['period_end']:
            #     period_start = self.pool.get('account.period').browse(self.cr, self.uid, data['form']['period_start'][0])
            #     period_end = self.pool.get('account.period').browse(self.cr, self.uid, data['form']['period_end'][0])
            #     domain_depreciation.append(('depreciation_date', '>=', period_start.date_start))

                # domain_depreciation.append(('depreciation_date','<=', period_end.date_stop))

            # elif data['form']['current_period']:
            #     period = self.pool.get('account.period').browse(self.cr, self.uid, data['form']['current_period'][0])
            #     domain_depreciation.append(('depreciation_date', '>=', period.date_start))
            #     domain_depreciation.append(('depreciation_date', '<=', period.date_stop))

            depreciation_ids = depreciation_asset_pool.search(domain_depreciation).ids
            if depreciation_ids:
                self.env.cr.execute('''
                    SELECT
                        aa.name, an.name, a.inventory_number, a.name, a.value, a.subscribe_date,  a.depreciation_tax, SUM(dp.amount), a.unsubscribe_date
                    FROM
                        account_asset_asset a, account_asset_depreciation_line dp, l10n_cu_resp_area ra, account_analytic_account an, account_account aa
                    WHERE 
                        dp.move_check AND dp.asset_id = a.id AND a.area = ra.id AND ra.account_depreciation_expense_id = aa.id AND ra.account_analytic_id = an.id
                        AND a.id in %s AND a.type2 = 'intangible' AND dp.id in %s
                    GROUP BY 
                        aa.name, an.name, a.inventory_number, a.name, a.value, a.subscribe_date,  a.depreciation_tax, dp.depreciation_date, dp.amount, a.unsubscribe_date
                    ORDER BY 
                        aa.name, an.name, a.inventory_number, dp.depreciation_date''', (tuple(asset_ids), tuple(depreciation_ids),))
                r = self.env.cr.fetchall()
                if r:
                    temp = []
                    cuenta = r[0][0]
                    for a in r:
                        if a[0] == cuenta:
                            temp.append(a)
                        else:
                            listIds.append(temp)
                            cuenta = a[0]
                            temp = []
                            temp.append(a)
                    listIds.append(temp)

                    temp1 = []
                    costo = listIds[0][0][1]
                    for b in listIds:
                        if b[0][1] == costo:
                            temp1.append(b)
                        else:
                            listres.append(temp1)
                            costo = b[0][1]
                            temp1 = []
                            temp1.append(b)
                    listres.append(temp1)
        # return listres
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'data': data['form'],
            'listres': listres
        }