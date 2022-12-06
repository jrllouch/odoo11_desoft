# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
import odoo.tools.float_utils as fu
import time
import datetime
from dateutil.relativedelta import relativedelta


class l10n_cu_AccountClose(models.TransientModel):
    _name = 'l10n_cu.account.close'
    _description = 'Account close'

    module_id = fields.Many2one('ir.module.module', 'Module', required=True)
    close_type = fields.Selection([('initial_load', 'Initial Load'),
                                   ('period_lock', 'Period Lock')])
    balance_ids = fields.One2many('l10n_cu.account.close.balance','account_close_id','Account balance', readonly=True)
    message = fields.Text('Message')
    close_valid = fields.Boolean('Close valid')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], readonly=True, default="draft")
    asset_lock_date = fields.Date(string='Lock Date for All Users')
    message = fields.Text('Message')

    @api.model
    def default_get(self, fields_list):
        defaults = super(l10n_cu_AccountClose, self).default_get(fields_list)
        module_id = defaults.get('module_id', False)
        message = ''
        if module_id and not self._is_not_valid(defaults):
            self._validate_close(defaults)
            if defaults.get('close_valid', False):
                message += _('Your system is ready to close.\n')
        else:
            if not defaults.get('message', False):
                message += _("Close invalid.\n")
            defaults.update(balance_ids=False, close_valid=False)

        if message:
            defaults.update(message=message)

        return defaults

    @api.model
    def _is_not_valid(self, defaults):
        invalid = False
        company_id = self.env.user.company_id
        if company_id.asset_lock_date and self.asset_lock_date and self.asset_lock_date < company_id.asset_lock_date:
            message=''
            message += _("Specified asset lock date must be after " + company_id.asset_lock_date)
            defaults['close_valid'] = False
            defaults['message'] = message
            invalid = True
        return invalid

    @api.model
    def _validate_close(self, defaults):
        message = ''
        company_id = self.env.user.company_id.id
        defaults.update({'balance_ids': False,
                         'close_valid': True})
        context = dict(self.env.context)
        module_id = self.env['ir.module.module'].search([('name', '=', 'l10n_cu_account_asset')], limit=1)
        account_obj = self.env['account.account']
        report_obj = self.env['report.account.report_trialbalance']
        defaults['close_valid'] = True
        asset_obj = self.env['account.asset.asset']
        last_day_month = datetime.date.today() + relativedelta(day=31)
        line_ids = []

        context.update({'state': 'all'})
        assets = asset_obj.search([('company_id', '=', company_id), ('state', 'in', ('open', 'stop', 'idler')),
                                   ('type', 'not in', ('module', 'functional'))])
        if assets:
            account_balance = {}
            for asset in assets:
                asset_account = asset.category_id.account_asset_id.id
                asset_depreciation_account = asset.category_id.account_depreciation_id.id
                if not asset_account:
                    defaults['close_valid'] = False
                    message += _(
                        "Asset (%s) has no asset account configured. Define an asset account for its category "
                        "(%s).") % (asset.name, asset.category_id.name)
                elif not asset_depreciation_account:
                    defaults['close_valid'] = False
                    message += _(
                        "Asset (%s) has no depreciation account configured. Define an depreciation account for its "
                        "category (%s).") % (asset.name, asset.category_id.name)
                else:
                    if asset_account in account_balance.keys():
                        account_balance[asset_account] = account_balance[asset_account] + asset.value
                    else:
                        account_balance[asset_account] = asset.value
                    if asset_depreciation_account in account_balance.keys():
                        account_balance[asset_depreciation_account] = account_balance[asset_depreciation_account] + \
                                                                      asset.value_amount_depreciation
                    else:
                        account_balance[asset_depreciation_account] = asset.value_amount_depreciation
            if defaults['close_valid']:
                flag = True
                precision_digits = self.env['decimal.precision'].precision_get('Account')
                for account_id, amount in account_balance.items():
                    account = account_obj.browse(account_id)
                    balance = report_obj._get_accounts(account, 'all')[0]['balance']
                    dif = fu.float_round(abs(abs(balance) - amount), precision_digits)
                    line_ids.append((0, 0, {'account_id': account.id, 'module_balance': amount,
                                            'account_balance': abs(balance), 'difference': dif}))

                    if not fu.float_is_zero(dif, precision_digits):
                        flag = False
                if not flag:
                    defaults['close_valid'] = False
                    message += _("There are differences between the balance reported for assets and reported by "
                                 "accounting for some accounts. Please must update the account balance to close the"
                                 " initial load of your company.")
        else:
            account_ids = account_obj.search([('internal_type', 'in', ('assets', 'regulatory_assets'))])
            for account in account_ids:
                balance = report_obj._get_accounts(account, 'all')
                if balance:
                    defaults['close_valid'] = False
                    message += _("You can not close the initial loading because there are asset accounts and asset "
                                 "regulatories accounts with balance.")
                    line_ids.append((0, 0, {'account_id': account.id, 'module_balance': 0.00,
                                            'account_balance': abs(balance),
                                            'difference': abs(balance)}))
        defaults['balance_ids'] = line_ids
        if not defaults['close_valid']:
            defaults['message'] = message

        if self.close_type == 'period_lock':
            depreciation_line_ids = self.env['account.asset.depreciation.line'].search(
                [('depreciation_date', '<=', self.asset_lock_date),
                 ('state', '!=', 'posted')])

            move_line_ids = self.env['l10n_cu.asset.move'].search([('operation_date', '<=', self.asset_lock_date),
                                                                   ('state', 'not in', ('draft', 'confirmed'))])
            if depreciation_line_ids:
                message +=_('Every depreciation line with depreciation date before the asset lock date (%s) must be posted') % self.asset_lock_date

                if move_line_ids:
                    message +=_('Every asset move with operation date before the asset lock date (%s) must be terminated or cancelled') % self.asset_lock_date

        defaults['message'] = message

    @api.one
    def history_asset(self, asset, context=None):
        history_obj = self.env['account.asset.history']

        history_vals = {
            'name': _('Initial Loading'),
            'modification_type': 5,
            'asset_id': asset.id,
            'asset_name': asset.name,
            'asset_category_group': asset.asset_category_group,
            'company_id': asset.company_id.id,
            'method': asset.method,
            'method_time': asset.method_time,
            'method_period': asset.method_period,
            'method_end': asset.method_end,
            'method_progress_factor': asset.method_progress_factor,
            'user_id': self.env.user.id,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'inventory_number': asset.inventory_number,
            'category_id': asset.category_id.id,
            'previous_value': 0.00,
            'value': asset.value,
            'purchase_date': asset.purchase_date,
            'depreciated': asset.depreciated,
            'paralyzed': True if asset.state == 'stop' else False,
            'state': asset.state,
            'depreciation_tax': asset.depreciation_tax,
            'value_amount_depreciation': asset.value_amount_depreciation,
        }

        if asset.asset_category_group == '4':
            hist_extra = {
                'transport_country': asset.transport_country.id,
                'equipment_type': asset.equipment_type.id,
                'transport_serial_number': asset.transport_serial_number,
                'transport_chassis_number': asset.transport_chassis_number,
                'transport_number_motor': asset.transport_number_motor,
                'transport_power': asset.transport_power,
                'transport_model': asset.transport_model,
                'transport_mark': asset.transport_mark,
                'transport_tonnage': asset.transport_tonnage,
                'transport_manufacture_date': asset.transport_manufacture_date,
                'transport_fuel_type': asset.transport_fuel_type,
                'transport_chapa': asset.transport_chapa
            }
            history_vals.update(hist_extra)
            asset_history_id = history_obj.create(history_vals, context)

            add_rep_hist_obj = self.env['l10n_cu.additions.replacements.history']
            add_rep_obj = self.env['l10n_cu.additions.replacements']
            for a in asset.transport_add_ids:
                add_rep = add_rep_obj.browse(a.id)
                add_rep_hist_id = add_rep_hist_obj.create({'additions': add_rep.additions,
                                                           'replacements': add_rep.replacements})
                add_rep_hist_obj.write(add_rep_hist_id, {'asset_history_id': asset_history_id})

        elif asset.asset_category_group == '2':
            hist_extra = {
                'furniture_country': asset.furniture_country.id,
                'furniture_type': asset.furniture_type.id,
                'furniture_serial_number': asset.furniture_serial_number,
                'furniture_model': asset.furniture_model,
                'furniture_mark': asset.furniture_mark
            }
            history_vals.update(hist_extra)
            history_obj.create(history_vals)

        elif asset.asset_category_group == '6':
            hist_extra = {
                'animals_purpose': asset.animals_purpose,
                'animals_identification': asset.animals_identification
            }
            history_vals.update(hist_extra)
            history_obj.create(history_vals)

        elif asset.asset_category_group == '1':
            hist_extra = {
                'expansions_modernizations': asset.expansions_modernizations
            }
            history_vals.update(hist_extra)
            history_obj.create(history_vals)
        else:
            history_obj.create(history_vals)

    @api.multi
    def confirm_close(self):
        self.ensure_one()
        context = dict(self.env.context)
        asset_obj = self.env['account.asset.asset']
        company_id = self.env.user.company_id
        asset_lock_date = company_id.asset_lock_date
        asset_ids = asset_obj.search([('company_id', '=', company_id.id),
                                      ('type', 'not in', ('module', 'functional')),
                                      ('state', 'in', ('draft', 'open', 'stop', 'idler'))])
        company_id.write({'asset_lock_date': self.asset_lock_date})
        if not asset_lock_date:
            asset_ids.filtered(lambda r: r.state == 'open').compute_depreciation_board()
            for asset in asset_ids:
                if asset.state == 'draft':
                    asset.write({'area': False})
                else:
                    self.history_asset(asset, context)
                    asset.write({'sub_ledger_number': self.env['ir.sequence'].get('sub.ledger.seq'), 'state': asset.state})
            area_obj = self.env['l10n_cu.resp.area']
            for area in area_obj.browse():
                area.write({})
        return {'type': 'ir.actions.act_window_close'}


class l10n_cu_AccountCloseBalance(models.TransientModel):
    _name = 'l10n_cu.account.close.balance'
    _description = 'Account close balance'

    account_close_id = fields.Many2one('l10n_cu.account.close', 'Account close', ondelete='cascade')
    account_id = fields.Many2one('account.account', 'Account', required=True, readonly=True)
    account_balance = fields.Float(string='Account balance', readonly=True)
    module_balance = fields.Float(string='Module balance', readonly=True)
    difference = fields.Float(string='Difference', readonly=True)
