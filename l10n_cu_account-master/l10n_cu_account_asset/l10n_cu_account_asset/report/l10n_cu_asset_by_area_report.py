# -*- coding: utf-8 -*-
'''
    This file contains the code to print the "Asset by responsibility area" Report
'''
from odoo import models, fields, api


class l10n_cu_asset_by_area_report(models.AbstractModel):
    _name = 'report.l10n_cu_account_asset.l10n_cu_asset_by_area_report'

    @api.model
    def get_report_values(self, docids, data=None):
        asset_pool = self.env['account.asset.asset']
        company_id = self.env.user.company_id

        domain_asset = [('company_id', '=', company_id.id),
                        ('state', 'in', ('open', 'idler', 'stop')),
                        ('parent_id', '=', False)]
        area = data['form']['area']
        asset_report = data['form']['asset_report']
        asset_module_report = data['form']['asset_module_report']
        category_id = data['form']['category_id']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']

        if area:
            domain_asset.append(('area', '=', area))

        if asset_report:
            domain_asset.append(('id', '=', asset_report))

        if asset_module_report:
            domain_asset.append(('id', '=', asset_module_report))

        if category_id:
            domain_asset.append(('category_id', '=', category_id))

        if start_date:
            domain_asset.append(('purchase_date', '>=', start_date))
        if end_date:
            domain_asset.append(('purchase_date', '<=', end_date))

        assets = asset_pool.search(domain_asset)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'data': data['form'],
            'assets': assets,
        }