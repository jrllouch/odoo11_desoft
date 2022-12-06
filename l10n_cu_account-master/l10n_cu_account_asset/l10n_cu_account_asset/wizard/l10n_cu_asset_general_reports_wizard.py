# -*- coding: utf-8 -*-
from odoo import fields, models, api
import time
from datetime import date, datetime


class l10n_cu_AssetGeneralReports(models.TransientModel):
    _name = "l10n_cu_asset.general.reports"
    _description = "Asset General Reports"

    @api.model
    def _get_default_start_date(self):
        return datetime.today().replace(day=1)

    reports = fields.Selection([('01', 'Fully Depreciated Assets'),
                                ('02', 'Assets by responsibility area'),
                                ('03', 'Reports of High'),
                                ('04', 'Reports of Low'),
                                ('05', 'Assets Transfers'),
                                ('06', 'Rented assets'),
                                ('07', 'Reevaluation'),
                                ('08', 'General Reparation'),
                                ('09', 'Listed Inventory Number'),
                                ('10', 'Account - Subaccount Balances'),
                                ('11', 'Monthly depreciation register'),
                                ('12', 'Monthly amortization register'),
                                ('13', 'Account Balances')], 'Reports')
    filter_cmp = fields.Selection(
        [('filter_no', 'No Filters'), ('filter_area', 'Area'), ('filter_category', 'Category'),
         ('filter_dates', 'Dates'),
         ('filter_asset', 'Asset'), ('filter_asset_module', 'Asset Module'),
         ('filter_both', 'All filters')], 'Filter by', required=True, default='filter_no')
    area = fields.Many2one('l10n_cu.resp.area', 'Area of responsibility')
    category_id = fields.Many2one('account.asset.category', 'Asset category',
                                  domain="[('internal_type', '!=', 'view')]")
    start_date = fields.Date('Date start')
    end_date = fields.Date('Date end')
    asset_report = fields.Many2one('account.asset.asset', 'Asset')
    asset_module_report = fields.Many2one(
        'account.asset.asset', 'Asset Module')

    @api.multi
    @api.onchange('reports')
    def onchange_report(self):
        if self.reports == '13':
            self.filter_cmp = 'filter_no'

    @api.multi
    @api.onchange('filter_cmp')
    def on_change_filter(self):
        if self.filter_cmp == 'filter_no':
            self.area = False
            self.category_id = False
        elif self.filter_cmp == 'filter_area':
            self.area = False
        elif self.filter_cmp == 'filter_asset':
            self.asset_report = False
        elif self.filter_cmp == 'filter_asset_module':
            self.asset_module_report = False
        elif self.filter_cmp == 'filter_category':
            self.category_id = False
        elif self.filter_cmp == 'filter_dates':
            self.start_date = date.today().replace(day=1)
            self.end_date = date.today()
        # elif self.filter_cmp in ('filter_period', 'filter_both'):
        #     # and self.fiscal_year_id:
        #     # start_period = end_period = False
        #     self.env.cr.execute('''
        #         SELECT * FROM (SELECT p.id
        #                        FROM account_period p
        #                        LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
        #                        WHERE f.id = %s
        #                        AND p.special = false
        #                        ORDER BY p.date_start ASC, p.special ASC
        #                        LIMIT 1) AS period_start
        #         UNION ALL
        #         SELECT * FROM (SELECT p.id
        #                        FROM account_period p
        #                        LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
        #                        WHERE f.id = %s
        #                        AND p.date_start < NOW()
        #                        AND p.special = false
        #                        ORDER BY p.date_stop DESC
        #                        LIMIT 1) AS period_stop''', (self.fiscal_year_id, self.fiscal_year_id))
        #     periods = [i[0] for i in self.env.cr.fetchall()]
        #     if periods and len(periods) > 1:
        #         self.period_start = periods[0]
        #         self.period_end = periods[1]
        #     if self.area and self.filter_cmp == 'filter_period':
        #         self.area = False

    @api.multi
    @api.onchange('start_date', 'end_date')
    def on_change_dates(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("The start period (%s) can't be greater than the end period (%s)!") \
                    % (self.start_date, self.end_date)

    @api.multi
    def print_report(self):
        self.ensure_one()
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'reports': self.reports,
                'category_id': self.category_id.name,
                'area': self.area.name,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'asset_module_report': self.asset_module_report.id,
                'asset_report': self.asset_report.id,
                'filter_cmp': self.filter_cmp,
            },
        }

        if self.reports == '01':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_fully_depreciated_assets_report').report_action(self,
                                                                                                                      data=data)
        if self.reports == '02':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_asset_by_area_report').report_action(self, data=data)

        if self.reports == '03':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_high_report').report_action(self, data=data)

        if self.reports == '04':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_low_report').report_action(self, data=data)

        if self.reports == '05':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_assets_transfers_report').report_action(self, data=data)

        if self.reports == '06':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_rented_assets_report').report_action(self, data=data)

        if self.reports == '07':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_reevaluation_report').report_action(self, data=data)

        if self.reports == '08':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_general_reparation_report').report_action(self, data=data)

        if self.reports == '09':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_listed_inventory_number_report').report_action(self, data=data)

        if self.reports == '10':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_account_subaccount_balances_report').report_action(self, data=data)

        if self.reports == '11':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_month_depreciation_report').report_action(self, data=data)

        if self.reports == '12':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_month_amortization_report').report_action(self, data=data)

        if self.reports == '13':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_account_balances_report').report_action(self, data=data)
