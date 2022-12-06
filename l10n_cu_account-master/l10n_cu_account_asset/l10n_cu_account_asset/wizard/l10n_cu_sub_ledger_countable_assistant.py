# -*- coding: utf-8 -*-
from odoo import fields, models, api
from datetime import date


class l10n_cuSubLedgerCountableAssistant(models.Model):
    _name = 'l10n_cu_account_asset.sub.ledger.countable.assistant'

    asset_id = fields.Many2one('account.asset.asset', 'Asset')
    # asset_category_group = fields.Char("Category group", related=asset_id.asset_category_group)
    # depreciation_tax = fields.Integer('Depreciation tax', related=asset_id.depreciation_tax)
    # sub_ledger_number = fields.Char('Sub-Ledger Number', related=asset_id.sub_ledger_number)
    # inventory_number = fields.Char("Number of inventory", related=asset_id.inventory_number)
    # asset_name = fields.Char('Name', related=asset_id.name)
    # area_name = fields.Char('Area Name', related=asset_id.area.name)
    # subscribe_date = fields.Date('Date of subscribe', related=asset_id.subscribe_date)

    # def _get_fiscal_year(self):
    #     now = time.strftime('%Y-%m-%d')
    #     fiscal_years = self.pool.get('account.fiscalyear').search([('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
    #     return fiscal_years and fiscal_years[0] or False

    # def get_initial_date(self):
    #     fiscal_year_id = self._get_fiscal_year(context)
    #     cr.execute('''
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
    #                        LIMIT 1) AS period_stop''', (fiscal_year_id, fiscal_year_id))
    #     periods = [i[0] for i in cr.fetchall()]
    #     if periods and len(periods) > 1:
    #         return periods[0]
    #
    # def get_final_date(self):
    #     fiscal_year_id = self._get_fiscal_year(context)
    #     cr.execute('''
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
    #                        LIMIT 1) AS period_stop''', (fiscal_year_id, fiscal_year_id))
    #     periods = [i[0] for i in cr.fetchall()]
    #     if periods and len(periods) > 1:
    #         return periods[1]

    # @api.model
    # def get_initial_date(self):
    #     period_obj = self.pool.get('account.period')
    #     period_ids = period_obj.find(time.strftime('%Y-%m-%d'))
    #     period = period_obj.browse(period_ids)
    #     return period.date_start

    # def get_final_date(self):
    # period_obj = self.pool.get('account.period')
    # period_ids = period_obj.find(time.strftime('%Y-%m-%d'))
    # period = period_obj.browse(period_ids)
    # return period.date_stop
    # return period.date_stop

    initial_date = fields.Date('Initial Date', default=date.today())
    # , default=get_initial_date)
    final_date = fields.Date('Final Date', default=date.today())

    # , default=get_final_date)

    @api.multi
    def accept(self, data):
        self.ensure_one()
        data.update({
            'ids': self.ids,
            'model': self._name,
            'form': {
                'initial_date': self.initial_date,
                'final_date': self.final_date,
                'asset_id': self.asset_id.id,
                'asset_category_group': self.asset_id.asset_category_group,
                'depreciation_tax': self.asset_id.depreciation_tax,
                'sub_ledger_number': self.asset_id.sub_ledger_number,
                'inventory_number': self.asset_id.inventory_number,
                'name': self.asset_id.name,
                'area': self.asset_id.area.name,
                'subscribe_date': self.asset_id.subscribe_date,
            },
        })

        return self.env.ref('l10n_cu_account_asset.report_l10n_cu_sub_ledger_asset_countable_report'). \
            report_action(self, data=data)
