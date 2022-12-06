import time
from odoo import fields, models, api, exceptions, _


class l10n_cu_AssetChangeAccount(models.Model):
    _name = 'l10n_cu.asset.change.account'
    _description = "Change the asset and deprc/amort accounts to the asset category"

    account_asset_id = fields.Many2one('account.account', 'Asset account',
                                       domain="[('type', '=', 'assets'), "
                                              "('company_id', '=', company_id)]")
    account_depreciation_id = fields.Many2one('account.account', 'Depreciation/amortization account',
                                              domain="[('type', '=', 'regulatory_assets'),"
                                                     "('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', 'Company', required=False, default=lambda s: s.env.user.company_id)

    @api.multi
    def change_accounts(self):
        self.ensure_one()
        context = dict(self.env.context)
        category = self.env['account.asset.category'].browse(context.get('active_id'))

        data = dict({
            'ids': context.get('active_ids', []),
            'model': context.get('active_model', 'ir.ui.menu'),
            'form': False,
            'extra': False
        })

        data['form'] = self.read(['account_asset_id', 'account_depreciation_id'])[0]
        if not data['form']['account_asset_id'] and not data['form']['account_depreciation_id']:
            raise exceptions.except_orm('Error', _('You must to select at least one account.'))
        if data['form']['account_asset_id'] and category.account_asset_id.id == data['form']['account_asset_id'][0]:
            raise exceptions.except_orm('Error', _('The asset account (%s) can not be the same of the category.')
                                        % (category.account_asset_id.name))
        if data['form']['account_depreciation_id'] and category.account_depreciation_id.id == \
                data['form']['account_depreciation_id'][0]:
            raise exceptions.except_orm('Error', _('The depreciation account (%s) can not be the same of the category.')
                                        % category.account_depreciation_id.name)

        return {
            'name': "Generating Account Move",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'wizard': True,
                'category_id': context.get('active_id'),
                'new_account_asset_id': data['form']['account_asset_id'] and data['form']['account_asset_id'][
                    0] or False,
                'new_account_depreciation_id': data['form']['account_depreciation_id'] and 
                                               data['form']['account_depreciation_id'][0] or False,
                'active_model': 'l10n_cu.asset.change.account',
                'active_id': self.id,
            }
        }

    @api.multi
    def _prepare_account_move(self, defaults):
        self.ensure_one()
        defaults['module'] = 'l10n_cu_asset'
        account_period = self.env['account.period.module']
        defaults['journal_id'] = self.company_id.asset_journal_id.id
        defaults['period_id'] = account_period._get_active_period('l10n_cu_asset', self.company_id.id).period_id.id
        self._prepare_change_account_move(defaults)

    @api.model
    def _prepare_change_account_move(self, change_account, defaults):
        lines = []
        context = dict(self.env.context)
        company_currency = change_account.company_id.currency_id.id
        current_currency = change_account.company_id.asset_journal_id.currency.id
        currency = company_currency != current_currency and current_currency or False

        category = self.env['account.asset.category'].browse(context.get('category_id'))
        defaults['narration'] = _('Changing the accounts for the category %s') % category.name
        
        if change_account.account_asset_id.id:
            value = 0.00
            for asset in category.asset_ids:
                value += asset.value
            amount_currency = currency and company_currency.compute(current_currency, company_currency,
                                                                    abs(value)) or False
            lines.append(self.env['l10n_cu.asset.move']._prepare_move_line(change_account.account_asset_id.id, abs(value), 
                                                                      'debit', {}, currency, amount_currency))
            lines.append(self.env['l10n_cu.asset.move']._prepare_move_line(category.account_asset_id.id, abs(value), 
                                                                      'credit', {}, currency, amount_currency))
        if change_account.account_depreciation_id.id:
            value = 0.00
            for asset in category.asset_ids:
                value += asset.value_amount_depreciation
            amount_currency = currency and company_currency.compute(current_currency, company_currency,
                                                                    abs(value)) or False
            lines.append(self.env['l10n_cu.asset.move']._prepare_move_line(change_account.account_depreciation_id.id, 
                                                                      abs(value), 'credit', {}, currency, 
                                                                      amount_currency))
            lines.append(self.env['l10n_cu.asset.move']._prepare_move_line(category.account_depreciation_id.id, abs(value), 
                                                                      'debit', {}, currency, amount_currency))

        defaults['line_id'] = [(0, 0, line) for line in lines]

    @api.multi
    def _confirm_account_move(self, account_move):
        self.ensure_one()
        if self:
            current_period = self.env['account.period.module']._get_active_period('l10n_cu_asset', self.company_id.id)
            date_start = current_period.period_id.date_start
            date_stop = current_period.period_id.date_stop
            if account_move.date < date_start or account_move.date > date_stop:
                raise exceptions.except_orm(_('Error !'), _('The operation date (%s) must be in the current period '
                                                            '(%s - %s)') % (account_move.date, date_start, date_stop))
            self._confirm_asset_change_category(account_move)

    @api.model
    def _confirm_asset_change_category(self, account_move):
        context = dict(self.env.context)
        if account_move:
            category = self.env['account.asset.category'].browse(context.get('category_id'))
            category.write({
                'account_asset_id': context.get('new_account_asset_id') and context.get(
                    'new_account_asset_id') or category.account_asset_id.id,
                'account_depreciation_id': context.get('new_account_depreciation_id') and context.get(
                    'new_account_depreciation_id') or category.account_depreciation_id.id
            })
