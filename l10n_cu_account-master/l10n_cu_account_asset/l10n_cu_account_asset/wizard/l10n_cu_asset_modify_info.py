# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError, Warning


class l10n_cu_AssetModifyInfo(models.Model):
    _name = 'l10n_cu.asset.modify.info'
    _description = "Modify asset information"

    @api.multi
    def _get_asset(self):
        context = dict(self.env.context)
        if context.get('active_id', False):
            asset_obj = self.env['account.asset.asset'].browse(context.get('active_id'))
            return asset_obj.id
        return False

    account_asset_id = fields.Many2one('account.account', 'Counterpart account',
                                       domain="[('internal_type', '=', 'other'),"
                                              " ('company_id', '=',company_id)]", required=False)
    asset_id = fields.Many2one('account.asset.asset', 'Asset', default=_get_asset)
    update_date = fields.Datetime('Update date', required=True)
    modification_type = fields.Selection([(1, 'Sub ledger data and/or category'),
                                          (2, 'Reevaluate'),
                                          (3, 'Depreciation data'),
                                          (4, 'Others'),
                                          (5, 'Initial'),
                                          (6, 'Asset Depreciation'),
                                          (8, 'Depreciation Value')], 'Modification type',
                                         help="Select the type of modification you desire to do.", required=True)
    category_id = fields.Many2one('account.asset.category', 'Asset category',
                                  help='Represent the category to belong the asset')
    value = fields.Float('Gross Value')
    depreciated = fields.Boolean('Depreciate')
    paralyzed = fields.Boolean('Paralyze')
    method_period = fields.Selection([(1, 'Monthly'), (2, 'Bimonthly'), (3, 'Every three months'),
                                      (4, 'Every four months'), (6, 'Semestral'), (12, 'Annual')], 'Period length',
                                     help="Represents the estimated time in months between the depreciation of a period.")
    depreciation_tax = fields.Integer('Depreciation tax', default=1)
    method = fields.Selection([('linear', 'Linear'), ('degressive', 'Degressive')], 'Computation Method',
                              help="Choose the method to use to compute the amount of depreciation lines.\n" \
                                   "  * Linear: Calculated on basis of: Gross Value / Number of Depreciations\n" \
                                   "  * Degressive: Calculated on basis of: Residual Value * Degressive Factor")
    method_progress_factor = fields.Float('Degressive Factor')
    inventory_number = fields.Char("Inventory number", size=20)
    asset_name = fields.Char('Asset name')
    asset_category_group = fields.Char("Category group", default='0')
    purchase_date = fields.Date('Purchase date')
    transport_country = fields.Many2one('res.country', 'Country')
    equipment_type = fields.Many2one('l10n_cu.asset.machinery.type', 'Machinery type')
    transport_serial_number = fields.Char('Serial number', size=20)
    transport_chassis_number = fields.Char('Chassis number', size=20)
    transport_number_motor = fields.Char('Motor number', size=20)
    transport_power = fields.Float('Power')
    transport_model = fields.Char('Model', size=20)
    transport_mark = fields.Char('Mark', size=20)
    transport_tonnage = fields.Float('Tonnage')
    transport_manufacture_date = fields.Date('Manufacture date', size=20)
    transport_fuel_type = fields.Char('Fuel Type', size=20)
    transport_chapa = fields.Char('Plates', size=20)
    transport_add_ids = fields.Many2many('l10n_cu.additions.replacements', 'asset_modify_additions_rep_rel',
                                         'asset_modify_id', 'additions_rep_id', 'Additons and replacements',
                                         help='Space for the biggest attaches and their possible substitutions')
    furniture_country = fields.Many2one('res.country', 'Country')
    furniture_type = fields.Many2one('l10n_cu.asset.furniture.type', 'Furniture type')
    furniture_serial_number = fields.Char('Serial Number', size=20)
    furniture_model = fields.Char('Model', size=20)
    furniture_mark = fields.Char('Mark', size=20)
    animals_purpose = fields.Char('Purpose', size=20)
    animals_identification = fields.Char('Identification number', size=20)
    expansions_modernizations = fields.Text('Expansions and modernizations')
    cause = fields.Text('Cause', help='Introduce a note about the modification cause', required=True)
    company_id = fields.Many2one('res.company', 'Company', required=False, default=lambda s: s.env.user.company_id)
    user_id = fields.Many2one('res.users', 'User', default=lambda s: s.env.user.id)
    done = fields.Boolean('Done', default=False)
    value_amount_depreciation = fields.Float('Amount Depreciation')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        context = dict(self.env.context)
        res = super(l10n_cu_AssetModifyInfo, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                                   toolbar=toolbar,
                                                                   submenu=False)
        depreciate = self.env['account.asset.asset'].browse(context.get('active_id')).depreciated
        if 'modification_type' in res['fields']:
            res['fields']['modification_type']['selection'] = [
                (1, 'Datos del submayor y/o categoría'),
                (2, 'Reevaluación'),
                (3, 'Datos de depreciación'),
                (8, 'Valor de depreciación'),
                (4, 'Otros'),
            ]
        return res

    @api.multi
    @api.onchange('modification_type')
    def on_change_modification_type(self):
        res = {'value': {}}
        context = dict(self.env.context)
        if context.get('active_id', False):
            asset_obj = self.env['account.asset.asset'].browse(context.get('active_id'))
            # if modification_type in (5, 6):
            #     return {'value': {'modification_type': False}}
            if self.modification_type == 1:
                self.category_id = asset_obj.category_id

                if asset_obj.asset_category_group in ('3', '4'):
                    self.transport_country = asset_obj.transport_country.id
                    self.equipment_type = asset_obj.equipment_type.id
                    self.transport_serial_number = asset_obj.transport_serial_number
                    self.transport_chassis_number = asset_obj.transport_chassis_number
                    self.transport_number_motor = asset_obj.transport_number_motor
                    self.transport_power = asset_obj.transport_power
                    self.transport_model = asset_obj.transport_model
                    self.transport_mark = asset_obj.transport_mark
                    self.transport_tonnage = asset_obj.transport_tonnage
                    self.transport_manufacture_date = asset_obj.transport_manufacture_date
                    self.transport_fuel_type = asset_obj.transport_fuel_type
                    self.transport_chapa = asset_obj.transport_chapa
                    self.transport_add_ids = asset_obj.transport_add_ids
                elif asset_obj.asset_category_group == '2':
                    self.furniture_country = asset_obj.furniture_country.id
                    self.furniture_type = asset_obj.furniture_type.id
                    self.furniture_serial_number = asset_obj.furniture_serial_number
                    self.furniture_model = asset_obj.furniture_model
                    self.furniture_mark = asset_obj.furniture_mark
                elif asset_obj.asset_category_group == '6':
                    self.animals_purpose = asset_obj.animals_purpose
                    self.animals_identification = asset_obj.animals_identification
                elif asset_obj.asset_category_group == '1':
                    self.expansions_modernizations = asset_obj.expansions_modernizations

            elif self.modification_type == 2:
                self.value = asset_obj.value
            elif self.modification_type == 3:
                self.depreciation_tax = asset_obj.depreciation_tax
                self.depreciated = asset_obj.depreciated
                self.method = asset_obj.method
                self.paralyzed = True if asset_obj.state == 'stop' else False
                self.method_period = asset_obj.method_period
            elif self.modification_type == 4:
                self.asset_name = asset_obj.name
                self.inventory_number = asset_obj.inventory_number
                self.purchase_date = asset_obj.purchase_date
            elif self.modification_type == 8:
                self.value_amount_depreciation = asset_obj.value_amount_depreciation

    @api.multi
    @api.onchange('depreciation_tax')
    def on_change_depreciation_tax(self):
        '''
        Function that controls the change in the depreciation tax.
        @raise Warning: * If the depreciation rate is smaller or equal than 0
        @raise Warning: * If the depreciation rate is greater than 100
        '''
        if self.depreciation_tax <= 0 or self.depreciation_tax > 100:
            self.depreciation_tax = 1
            raise ValueError('The depreciation rate can not be smaller or equal than 0 or greater than to 100!')

    @api.multi
    @api.onchange('category_id')
    def on_change_category_id(self):
        if self.category_id:
            self.asset_category_group = self.category_id.group_id.code,

    @api.multi
    @api.onchange('depreciated')
    def on_change_depreciated(self):
        if not self.depreciated:
            self.paralyzed = False

    @api.multi
    @api.onchange('transport_manufacture_date')
    def on_change_transport_manufacture_date(self):
        if self.transport_manufacture_date:
            if datetime.strptime(self.transport_manufacture_date, '%Y-%m-%d') > datetime.now():
                transport_manufacture_date = self.transport_manufacture_date
                self.transport_manufacture_date = False
                raise Warning(_("The manufacture date (%s) can't be greater than the current date (%s)!") %
                              (transport_manufacture_date, datetime.strftime(datetime.now(), '%Y-%m-%d')))

    @api.multi
    @api.onchange('purchase_date')
    def on_change_purchase_date(self):
        if self.purchase_date:
            if datetime.strptime(self.purchase_date, '%Y-%m-%d') > datetime.now():
                purchase_date = self.purchase_date
                self.purchase_date = False
                raise Warning(_("The purchase_date (%s) can't be greater than the current date (%s)!") %
                              (purchase_date, datetime.strftime(datetime.now(), '%Y-%m-%d')))

    @api.multi
    def _prepare_account_move(self, defaults):
        self.ensure_one()
        defaults['module'] = 'l10n_cu_asset'
        defaults['asset_modification_id'] = self.id
        defaults['journal_id'] = self.asset_id.company_id.asset_journal_id.id
        self._prepare_modification_account_move(self, defaults)

    @api.model
    def _prepare_modification_account_move(self, defaults):
        lines = []
        company_currency = self.asset_id.company_id.currency_id.id
        current_currency = self.asset_id.company_id.asset_journal_id.currency.id
        currency = company_currency != current_currency and current_currency or False

        if self.modification_type == 2:
            defaults['narration'] = _('Reevaluating the asset %s') % (self.asset_id.name)
            value = self.value - self.asset_id.value
            nature = value > 0 and 'debit' or 'credit'
            amount_currency = currency and company_currency.compute(current_currency, company_currency,
                                                                    abs(value)) or False
            lines.append(self.env['l10n_cu.asset.move'].
                         _prepare_move_line(self.asset_id.category_id.account_asset_id.id, abs(value),
                                            nature, {}, currency, amount_currency))
            nature = nature == 'debit' and 'credit' or 'debit'
            lines.append(self.env['l10n_cu.asset.move'].
                         _prepare_move_line(self.account_asset_id.id, abs(value),
                                            nature, {}, currency, amount_currency))
        elif self.modification_type == 8:
            defaults['narration'] = _('Changing the depreciation value of the asset %s') % (self.asset_id.name)
            value = self.value_amount_depreciation - self.asset_id.value_amount_depreciation
            nature = value > 0 and 'credit' or 'debit'
            amount_currency = currency and company_currency.compute(current_currency, company_currency,
                                                                    abs(value)) or False
            lines.append(self.env['l10n_cu.asset.move'].
                         _prepare_move_line(self.asset_id.category_id.account_depreciation_id.id, abs(value),
                                            nature, {}, currency, amount_currency))
            nature = nature == 'debit' and 'credit' or 'debit'
            lines.append(self.env['l10n_cu.asset.move'].
                         _prepare_move_line(self.account_asset_id.id, abs(value),
                                            nature, {}, currency, amount_currency))
        else:
            defaults['narration'] = _('Changing the category of the asset %s') % (self.asset_id.name)
            value = self.asset_id.value
            nature = 'credit'
            amount_currency = currency and company_currency.compute(current_currency, company_currency, value) or False
            lines.append(self.env['l10n_cu.asset.move'].
                         _prepare_move_line(self.asset_id.category_id.account_asset_id.id, value,
                                            nature, {}, currency, amount_currency))
            nature = 'debit'
            lines.append(self.env['l10n_cu.asset.move'].
                         _prepare_move_line(self.category_id.account_asset_id.id, value, nature, {},
                                            currency, amount_currency))
            if self.asset_id.value - self.asset_id.value_residual != 0.00:
                value = self.asset_id.value - self.asset_id.value_residual
                nature = 'credit'
                amount_currency = currency and company_currency.compute(current_currency, company_currency,
                                                                        value) or False
                lines.append(self.env['l10n_cu.asset.move'].
                             _prepare_move_line(self.category_id.account_depreciation_id.id,
                                                value, nature, {}, currency, amount_currency))
                nature = 'debit'
                lines.append(self.env['l10n_cu.asset.move'].
                             _prepare_move_line(self.asset_id.category_id.account_depreciation_id.id,
                                                value, nature, {}, currency, amount_currency))

        defaults['line_id'] = [(0, 0, line) for line in lines]

    @api.multi
    def _confirm_account_move(self, account_move):
        self.ensure_one()
        if self:
            self.asset_id.write({'sub_ledger_number': self.env['ir.sequence'].get('sub.ledger.seq')})
            self._confirm_asset_modification(account_move)

    @api.model
    def _confirm_asset_modification(self, account_move):
        # context = dict(self.env.context)
        self.ensure_one()
        if account_move:
            hist_vals = {
                'name': self.cause,
                'date': self.update_date,
                'user_id': self.env.user.id,
                'modification_type': self.modification_type,
                'asset_id': self.asset_id.id
            }
            if self.modification_type == 2:
                hist_vals['previous_value'] = self.asset_id.value
                hist_vals['value'] = self.value
                hist_vals['value_amount_depreciation'] = self.asset_id.value_amount_depreciation
                self.asset_id.write({'value': self.value})
            elif self.modification_type == 8:
                hist_vals['value_amount_depreciation'] = self.value_amount_depreciation
                self.asset_id.write({'value_amount_depreciation': self.value_amount_depreciation})
            else:
                # Aqui va cuando es cambio de categoria
                hist_vals['category_id'] = self.category_id.id
                hist_vals['asset_category_group'] = self.asset_category_group
                if self.asset_category_group == '1':
                    hist_vals['expansions_modernizations'] = self.expansions_modernizations
                    self.asset_id.write({'expansions_modernizations': self.expansions_modernizations,
                                         'category_id': self.category_id.id,
                                         'asset_category_group': self.asset_category_group})

                elif self.asset_category_group == '2':
                    hist_vals['furniture_country'] = self.furniture_country.id
                    hist_vals['furniture_type'] = self.furniture_type.id
                    hist_vals['furniture_serial_number'] = self.furniture_serial_number
                    hist_vals['furniture_model'] = self.furniture_model
                    hist_vals['furniture_mark'] = self.furniture_mark
                    self.asset_id.write({'furniture_country': self.furniture_country.id,
                                         'furniture_type': self.furniture_type.id,
                                         'furniture_serial_number': self.furniture_serial_number,
                                         'furniture_model': self.furniture_model,
                                         'furniture_mark': self.furniture_mark,
                                         'category_id': self.category_id.id,
                                         'asset_category_group': self.asset_category_group})

                elif self.asset_category_group in ('3', '4'):
                    hist_vals['transport_country'] = self.transport_country.id
                    hist_vals['equipment_type'] = self.equipment_type.id
                    hist_vals['transport_serial_number'] = self.transport_serial_number
                    hist_vals['transport_chassis_number'] = self.transport_chassis_number
                    hist_vals['transport_number_motor'] = self.transport_number_motor
                    hist_vals['transport_power'] = self.transport_power
                    hist_vals['transport_model'] = self.transport_model
                    hist_vals['transport_mark'] = self.transport_mark
                    hist_vals['transport_tonnage'] = self.transport_tonnage
                    hist_vals['transport_manufacture_date'] = self.transport_manufacture_date
                    hist_vals['transport_fuel_type'] = self.transport_fuel_type
                    hist_vals['transport_chapa'] = self.transport_chapa

                    asset_history_id = self.env['account.asset.history'].create(hist_vals)

                    self.asset_id.write({'transport_country': self.transport_country.id,
                                         'equipment_type': self.equipment_type.id,
                                         'transport_serial_number': self.transport_serial_number,
                                         'transport_chassis_number': self.transport_chassis_number,
                                         'transport_number_motor': self.transport_number_motor,
                                         'transport_power': self.transport_power,
                                         'transport_model': self.transport_model,
                                         'transport_mark': self.transport_mark,
                                         'transport_tonnage': self.transport_tonnage,
                                         'transport_manufacture_date': self.transport_manufacture_date,
                                         'transport_fuel_type': self.transport_fuel_type,
                                         'transport_chapa': self.transport_chapa,
                                         'category_id': self.category_id.id,
                                         'asset_category_group': self.asset_category_group})

                    add_rep_hist = self.env['l10n_cu.additions.replacements.history']
                    add_rep = self.env['l10n_cu.additions.replacements']
                    for a in self.transport_add_ids:
                        add_rep_obj = add_rep.browse(a.id)
                        add_rep_hist_id = add_rep_hist.create({'additions': add_rep_obj.additions,
                                                               'replacements': add_rep_obj.replacements})
                        add_rep_hist.write(add_rep_hist_id, {'asset_history_id': asset_history_id})
                        add_rep.write(a.id, {'asset_id': self.asset_id.id})

                elif self.asset_category_group == '6':
                    hist_vals['animals_purpose'] = self.animals_purpose
                    hist_vals['animals_identification'] = self.animals_identification
                    self.asset_id.write({'animals_purpose': self.animals_purpose,
                                         'animals_identification': self.animals_identification,
                                         'category_id': self.category_id.id,
                                         'asset_category_group': self.asset_category_group})

            if self.asset_category_group not in ('3', '4'):
                self.env['account.asset.history'].create(hist_vals)
            self.env['account.asset.asset'].compute_depreciation_board(self.asset_id.id)
            self.write({'done': True})

    @api.multi
    def _create_move(self):
        self.ensure_one()
        if not self.company_id.asset_journal_id:
            model_obj = self.env['ir.model.data']
            msg = _('You do not have an asset journal configured for your company.\n '
                    'Please, go to the asset configuration and select the asset journal.')
            action_id = model_obj._get_id('l10n_cu_account_asset', 'action_asset_config_settings')
            # raise exceptions.RedirectWarning(msg, action_id, _('Go to the asset configuration panel'))
        return {
            'name': "Generating Account Move",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'wizard': True,
                'active_model': 'l10n_cu.asset.modify.info',
                'active_id': self.id,
            }
        }

    @api.multi
    def modify_info(self):
        context = dict(self.env.context)
        self = self.sudo()
        data = dict({
            'ids': context.get('active_ids', []),
            'model': context.get('active_model', 'ir.ui.menu'),
            'form': False,
            'extra': False
        })
        data['form'] = self.read(['asset_id', 'update_date', 'modification_type', 'cause', 'user_id'])[0]
        asset_modify_obj = self.search([('done', '=', True), ('asset_id', '=', data['form']['asset_id'][0])], limit=1,
                                       order='id desc')
        update_date = datetime.strptime(data['form']['update_date'], '%Y-%m-%d %H:%M:%S')
        if asset_modify_obj:
            asset_lock_date = self.company_id.asset_lock_date
            if update_date <= datetime.strptime(asset_lock_date, '%Y-%m-%d'):
                raise Warning(_("The update date (%s) must be later than %s!") %
                              (update_date, asset_lock_date))
            if update_date < datetime.strptime(asset_modify_obj.update_date, '%Y-%m-%d %H:%M:%S'):
                raise Warning(_("The update date (%s) can't be less than the date of the last update (%s)!") %
                              (update_date, asset_modify_obj.update_date))
        if update_date > datetime.now():
            raise Warning(_("The update date (%s) can't be greater than the current date (%s)!") %
                          (update_date, datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')))
        else:
            asset = self.env['account.asset.asset']
            hist = self.env['account.asset.history']
            asset_obj = asset.browse(data['form']['asset_id'][0])
            asset_category_obj = self.env['account.asset.category']
            hist_vals = {
                'name': data['form']['cause'],
                'date': data['form']['update_date'],
                'user_id': data['form']['user_id'][0],
                'modification_type': data['form']['modification_type'],
                'asset_id': data['form']['asset_id'][0]
            }

            # Reevaluate
            if data['form']['modification_type'] == 2:
                data['extra'] = self.read(['value', 'account_asset_id'])[0]
                if data['extra']['value'] < asset_obj.value_residual:
                    raise Warning(
                        _("The new gross value (%s) can't be less than the residual value (%s) before modification!") %
                        (data['extra']['value'], asset_obj.value_residual))
                return self._create_move()

            # Depreciation Values
            elif data['form']['modification_type'] == 8:
                data['extra'] = self.read(['value_amount_depreciation', 'account_asset_id'])[0]
                if data['extra']['value_amount_depreciation'] > asset_obj.value:
                    raise Warning(
                        _("The new depreciation value (%s) can not be greater than the asset purchase value (%s)!") %
                        (data['extra']['value_amount_depreciation'], asset_obj.value))
                return self._create_move()

            # Depreciation data
            elif data['form']['modification_type'] == 3:
                data['extra'] = self.read(['depreciated', 'paralyzed', 'method_period', 'method',
                                           'depreciation_tax', 'method_progress_factor'])[0]
                hist_extra = {
                    'depreciated': data['extra']['depreciated'],
                    'paralyzed': data['extra']['paralyzed'],
                    'state': asset_obj.state if not data['extra']['paralyzed'] else 'stop',
                    'method_period': data['extra']['method_period'],
                    'method': data['extra']['method'],
                    'depreciation_tax': data['extra']['depreciation_tax'],
                }
                if data['extra']['method'] == 'degressive':
                    hist_extra.update({'method_progress_factor': data['extra']['method_progress_factor']})

                hist_vals.update(hist_extra)
                hist.create(hist_vals)
                self.write({'done': True})

                if data['extra']['paralyzed'] == False:
                    asset_obj.write({'depreciated': False,
                                     'method_period': data['extra']['method_period'],
                                     'method': data['extra']['method'],
                                     'depreciation_tax': data['extra']['depreciation_tax'],
                                     'method_progress_factor': data['extra']['method_progress_factor']
                                     })
                    if asset_obj.has_been_paralyzed:
                        asset_obj.write({'state': asset_obj.previous_state})
                    asset_obj.compute_depreciation_board()
                else:
                    asset_obj.write({'depreciated': True,
                                     'state': 'stop',
                                     'has_been_paralyzed': True})
                    asset_obj.delete_depreciation_board()

            # Others
            elif data['form']['modification_type'] == 4:
                data['extra'] = self.read(['asset_name', 'inventory_number', 'purchase_date'])[0]
                hist_extra = {
                    'asset_name': data['extra']['asset_name'],
                    'inventory_number': data['extra']['inventory_number'],
                    'purchase_date': data['extra']['purchase_date'],
                }
                hist_vals.update(hist_extra)
                hist.create(hist_vals)
                asset_name = data['extra']['asset_name']
                inventory_number = data['extra']['inventory_number']
                purchase_date = data['extra']['purchase_date']

                value = {'name': asset_name,
                         'inventory_number': inventory_number,
                         'purchase_date': purchase_date}

                asset_obj.update(value)

                self.write({'done': True})

            # Category
            else:
                data['extra'] = self.read(['category_id', 'asset_category_group'])[0]
                category_id = data['extra']['category_id'][0]
                asset_category_group = data['extra']['asset_category_group'][2]
                if asset_category_group in ('3', '4'):
                    data['extra'] = self.read(['transport_country', 'equipment_type',
                                               'transport_serial_number', 'transport_chassis_number',
                                               'transport_number_motor', 'transport_power',
                                               'transport_model', 'transport_mark', 'transport_tonnage',
                                               'transport_manufacture_date', 'transport_fuel_type',
                                               'transport_chapa', 'transport_add_ids'])[0]

                    if category_id == asset_obj.category_id.id:
                        hist_extra = {
                            'category_id': category_id,
                            'asset_category_group': asset_category_group,
                            'transport_country': data['extra']['transport_country'] and
                                                 data['extra']['transport_country'][0] or False,
                            'equipment_type': data['extra']['equipment_type'] and data['extra']['equipment_type'][
                                0] or False,
                            'transport_serial_number': data['extra']['transport_serial_number'],
                            'transport_chassis_number': data['extra']['transport_chassis_number'],
                            'transport_number_motor': data['extra']['transport_number_motor'],
                            'transport_power': data['extra']['transport_power'],
                            'transport_model': data['extra']['transport_model'],
                            'transport_mark': data['extra']['transport_mark'],
                            'transport_tonnage': data['extra']['transport_tonnage'],
                            'transport_manufacture_date': data['extra']['transport_manufacture_date'],
                            'transport_fuel_type': data['extra']['transport_fuel_type'],
                            'transport_chapa': data['extra']['transport_chapa'],
                        }
                        hist_vals.update(hist_extra)
                        asset_history_id = hist.create(hist_vals)
                        self.write({'done': True})

                        transport_add_ids = []
                        for lista in asset_obj.transport_add_ids:
                            if lista.id not in data['extra']['transport_add_ids']:
                                transport_add_ids.append([2, lista.id])
                        asset_obj.write({'transport_country': data['extra']['transport_country'] and
                                                              data['extra']['transport_country'][0] or False,
                                         'equipment_type': data['extra']['equipment_type'] and
                                                           data['extra']['equipment_type'][0] or False,
                                         'transport_serial_number': data['extra']['transport_serial_number'],
                                         'transport_chassis_number': data['extra']['transport_chassis_number'],
                                         'transport_number_motor': data['extra']['transport_number_motor'],
                                         'transport_power': data['extra']['transport_power'],
                                         'transport_model': data['extra']['transport_model'],
                                         'transport_mark': data['extra']['transport_mark'],
                                         'transport_tonnage': data['extra']['transport_tonnage'],
                                         'transport_manufacture_date': data['extra']['transport_manufacture_date'],
                                         'transport_fuel_type': data['extra']['transport_fuel_type'],
                                         'transport_chapa': data['extra']['transport_chapa'],
                                         'transport_add_ids': transport_add_ids})
                    else:
                        return self._create_move()
                    add_rep_hist_obj = self.env['l10n_cu.additions.replacements.history']
                    add_rep_obj = self.env['l10n_cu.additions.replacements']
                    for a in data['extra']['transport_add_ids']:
                        add_rep = add_rep_obj.browse(a)
                        add_rep_hist_id = add_rep_hist_obj.create({'additions': add_rep.additions,
                                                                   'replacements': add_rep.replacements})
                        add_rep_hist_obj.write({'asset_history_id': asset_history_id})
                        add_rep.write({'asset_id': data['form']['asset_id'][0]})

                elif asset_category_group == '2':
                    data['extra'] = self.read(['furniture_country', 'furniture_type',
                                               'furniture_serial_number', 'furniture_model',
                                               'furniture_mark'])[0]

                    if category_id == asset_obj.category_id.id:
                        hist_extra = {
                            'category_id': category_id,
                            'asset_category_group': asset_category_group,
                            'furniture_country': data['extra']['furniture_country'] and
                                                 data['extra']['furniture_country'][0] or False,
                            'furniture_type': data['extra']['furniture_type'] and
                                              data['extra']['furniture_type'][0] or False,
                            'furniture_serial_number': data['extra']['furniture_serial_number'],
                            'furniture_model': data['extra']['furniture_model'],
                            'furniture_mark': data['extra']['furniture_mark'],
                        }
                        hist_vals.update(hist_extra)
                        hist.create(hist_vals)
                        self.write({'done': True})

                        asset.write({'furniture_country': data['extra']['furniture_country'] and
                                                          data['extra']['furniture_country'][0] or False,
                                     'furniture_type': data['extra']['furniture_type'] and
                                                       data['extra']['furniture_type'][0] or False,
                                     'furniture_serial_number': data['extra']['furniture_serial_number'],
                                     'furniture_model': data['extra']['furniture_model'],
                                     'furniture_mark': data['extra']['furniture_mark']})
                    else:
                        return self._create_move()

                elif asset_category_group == '6':
                    data['extra'] = self.read(['animals_purpose', 'animals_identification'])[0]

                    if category_id == asset_obj.category_id.id:
                        hist_extra = {
                            'category_id': category_id,
                            'asset_category_group': asset_category_group,
                            'animals_purpose': data['extra']['animals_purpose'],
                            'animals_identification': data['extra']['animals_identification'],
                        }
                        hist_vals.update(hist_extra)
                        hist.create(hist_vals)
                        self.write({'done': True})

                        asset.write({'animals_purpose': data['extra']['animals_purpose'],
                                     'animals_identification': data['extra']['animals_identification']})
                    else:
                        return self._create_move()

                elif asset_category_group == '1':
                    data['extra'] = self.read(['expansions_modernizations'])[0]

                    if category_id == asset_obj.category_id.id:
                        hist_extra = {
                            'category_id': category_id,
                            'asset_category_group': asset_category_group,
                            'expansions_modernizations': data['extra']['expansions_modernizations'],
                        }
                        hist_vals.update(hist_extra)
                        hist.create(hist_vals)
                        self.write({'done': True})

                        asset.write({'expansions_modernizations': data['extra']['expansions_modernizations']})
                    else:
                        return self._create_move()
            asset_obj.write({'sub_ledger_number': self.env['ir.sequence'].get('sub.ledger.seq')})
