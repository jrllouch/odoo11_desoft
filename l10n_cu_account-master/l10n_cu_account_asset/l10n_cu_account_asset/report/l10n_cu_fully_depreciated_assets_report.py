# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
import calendar

class l10n_cu_fully_depreciated_assets_report(models.AbstractModel):
    _name = 'report.l10n_cu_account_asset.l10n_cu_fully_deprec_assets_report'
    '''
    This is the class who obtains and process the necessary
    data to show in the report document.
    '''

    @api.model
    def get_report_values(self, docids, data=None):
        asset_pool = self.env['account.asset.asset']
        company_id = self.env.user.company_id
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        move_ids = self.env['l10n_cu.asset.move'].search([('operation_date', '>=', start_date),
                                                          ('operation_date', '<=', end_date)]).ids
        asset_group_by_area = {}
        today = datetime.today()
        day = calendar.monthrange(today.year, today.month)[1]
        date_end = datetime.strptime(str(today.year) + "-" + str(today.month) + "-" + str(day), "%Y-%m-%d")
        domain_asset = [('company_id', '=', company_id.id),
                        ('state', 'in', ('open', 'idler', 'stop')),
                        ('parent_id', '=', False)]

        area = data['form']['area']
        asset_report = data['form']['asset_report']
        asset_module_report = data['form']['asset_module_report']
        category_id = data['form']['category_id']

        if area:
            domain_asset.append(('area', '=', area))

        if asset_report:
            domain_asset.append(('id', '=', asset_report))

        if asset_module_report:
            domain_asset.append(('id', '=', asset_module_report))

        if category_id:
            domain_asset.append(('category_id', '=', category_id))

        if start_date:
            domain_asset.append(('subscribe_date', '>=', start_date))
        if end_date:
            domain_asset.append(('subscribe_date', '<=', end_date))

        asset_ids = asset_pool.search(domain_asset).ids
        if asset_ids:
            self.env.cr.execute('''
                SELECT 
                  ar.name, a.name, a.value, a.inventory_number, a.subscribe_date, ar.name
                FROM 
                  account_asset_asset a, l10n_cu_resp_area ar
                WHERE 
                  a.area = ar.id AND (a.value - a.value_amount_depreciation) = 0
                GROUP BY
                  a.area, a.name, a.value, a.inventory_number, a.subscribe_date, ar.name
                ORDER BY
                  a.area, a.inventory_number''')
            r = self.env.cr.fetchall()
            if r:
                temp = []
                area_id = r[0][0]
                for a in r:
                    asset_group_by_area.setdefault(a[0], []).append(a)
                # if area_id in asset_group_by_area:

                    # if a[0] == area_id:
                    # asset_group_by_area[area_id].append(a)
                    # temp.append(a)
                    # else:

                    # asset_group_by_area.setdefault(area_id, [])
                    #     listIds.append(temp)
                # area_id = a[0]
                #     temp = []
                #     temp.append(a)
                # listIds.append(temp)0

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'data': data['form'],
            'group': asset_group_by_area,
        }