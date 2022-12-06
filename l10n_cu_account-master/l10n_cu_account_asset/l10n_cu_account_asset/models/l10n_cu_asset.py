# -*- coding: utf-8 -*-

import time
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons import decimal_precision as dp

ASSET_DEP_ARGS = (
    'area', 'receiver_name', 'method', 'depreciation_tax', 'method_period', 'method_progress_factor', 'depreciated')


# Alian

class l10n_cu_AssetCategoryGroup(models.Model):
    '''
    This class save the fixed asset category group
    '''
    _name = "l10n_cu.asset.category.group"
    _description = "Category groups"

    name = fields.Char('Name', required=True,
                       help='Name of the category group.')
    type = fields.Selection(
        [('tangible', 'Tangible'), ('intangible', 'Intangible'), ], 'Type')
    code = fields.Char('Code')


class l10n_cu_TemplateAccountAssetCategory(models.Model):
    _name = "l10n_cu.template.account.asset.category"
    _description = "Template Asset category"

    name = fields.Char(required=True, index=True, string="Asset Type")
    group_id = fields.Many2one('l10n_cu.asset.category.group', 'Group')
    depreciation_tax = fields.Integer('Depreciation tax', default=1)
    internal_type = fields.Selection([('view', 'View'), ('normal', 'Normal')], 'Internal Type', required=True,
                                     default='normal',
                                     help="'View' is for categories that are parent of other categories, 'Normal' "
                                          "is for categories with or without parent category and where is possible "
                                          "the definition of others data.")
    method = fields.Selection([('linear', 'Linear'), ('degressive', 'Degressive')], 'Computation Method',
                              default='linear',
                              help="Choose the method to use to compute the amount of depreciation lines.\n"
                                   "  * Linear: Calculated on basic of: Gross Value / Number of Depreciation\n"
                                   "  * Degressive: Calculated on basis of: Residual Value * Degressive Factor")
    parent_id = fields.Many2one('l10n_cu.template.account.asset.category', 'Parent asset category',
                                domain="[('internal_type', '=', 'view')]")

    register_module = fields.Boolean('Modules may include', default=1)


class AccountAssetCategory(models.Model):
    _name = 'account.asset.category'
    _inherit = 'account.asset.category'
    _description = "Asset category"

    @api.multi
    @api.depends('asset_valid')
    def _get_asset_valid(self):
        for category in self:
            category.asset_ids = self.env['account.asset.asset'].search([('category_id', '=', category.id),
                                                                         ('state', 'in',
                                                                          ('open', 'idler', 'stop'))
                                                                         ]) and True or False

    def _prepare_account_asset_category(self, temprec, company):
        existing_account = self.env['account.asset.category'].search(
            [('company_id', '=', company.id), ('name', '=', temprec.name)])
        parent_id = False
        if not existing_account:
            if temprec.parent_id:
                parent_id = self.env['account.asset.category'].search([('company_id', '=', company.id),
                                                                       ('name', '=', temprec.parent_id.name)])
            return {'name': temprec.name,
                    'group_id': temprec.group_id.id,
                    'depreciation_tax': temprec.depreciation_tax,
                    'internal_type': temprec.internal_type,
                    'parent_id': parent_id and parent_id.id or False,
                    'method': temprec.method,
                    'register_module': temprec.register_module,
                    'company_id': company.id}

    @api.multi
    def _create_account_asset_category(self, companies):
        template = self.env['l10n_cu.template.account.asset.category'].search([])
        for company in companies:
            for temp in template:
                vals = self._prepare_account_asset_category(temp, company) or False
                if vals:
                    self.env['account.asset.category'].create(vals)

    parent_id = fields.Many2one('account.asset.category', 'Parent asset category',
                                domain="[('internal_type', '=', 'view')]")
    child_ids = fields.One2many(
        'account.asset.category', 'parent_id', 'Children assets category')
    group_id = fields.Many2one('l10n_cu.asset.category.group', 'Group')
    internal_type = fields.Selection([('view', 'View'), ('normal', 'Normal')], 'Internal Type', required=True,
                                     default='normal',
                                     help="'View' is for categories that are parent of other categories, 'Normal' "
                                          "is for categories with or without parent category and where is possible "
                                          "the definition of others data.")
    register_module = fields.Boolean('Modules may include', default=1)
    register_functional_basic_unit = fields.Boolean(
        'Functional or Basic Unit may include', default=1)
    sequence_id = fields.Many2one('ir.sequence', 'Sequence',
                                  help="This field contains the information related to the numbering of the asset entries of this asset category.")
    journal_id = fields.Many2one('account.journal', 'Journal',
                                 domain="[('type', '=', 'general'), ('company_id', '=',company_id)]", required=False)
    account_depreciation_expense_id = fields.Many2one('account.account', string='Depreciation expense account',
                                                      domain=[('internal_type', '=', 'other')], required=False)
    account_depreciation_id = fields.Many2one(required=False,
                                              domain="[('internal_type','=','other'), ('deprecated', '=', False),('company_id', '=', company_id)]")
    account_asset_id = fields.Many2one(required=False,
                                       domain="[('internal_type','=','other'), ('deprecated', '=', False),('company_id', '=', company_id)]")

    company_id = fields.Many2one('res.company', 'Company', required=False)
    method = fields.Selection([('linear', 'Linear'), ('degressive', 'Degressive')], 'Computation Method',
                              help="Choose the method to use to compute the amount of depreciation lines.\n"
                                   "  * Linear: Calculated on basic of: Gross Value / Number of Depreciation\n"
                                   "  * Degressive: Calculated on basis of: Residual Value * Degressive Factor")
    method_period = fields.Selection([(1, 'Monthly'),
                                      (2, 'Bimonthly'),
                                      (3, 'Every three months'),
                                      (4, 'Every four months'),
                                      (6, 'Semestral'),
                                      (12, 'Annual')], 'Period length',
                                     help="Represents the estimated time in months between the depreciation of a period.",
                                     default=1)
    depreciation_tax = fields.Integer('Depreciation tax', default=1)
    asset_opening_done = fields.Boolean(related='company_id.asset_opening_done')
    asset_ids = fields.One2many(
        'account.asset.asset', 'category_id', 'Asset List')
    not_depreciate = fields.Boolean('Not Depreciate', default=False)
    asset_valid = fields.Boolean(
        function=_get_asset_valid, string='Valid assets')

    @api.constrains('name', 'company_id')
    def _check_name(self):
        '''
        Verify that the name of the asset category is not repeated in the company.
        '''
        count = self.search([('name', '=', self.name), ('company_id', '=', self.company_id.id)], count=True)
        if count > 1:
            raise ValidationError('The asset category name already exists in this company!')

    @api.multi
    def change_account(self):
        self.ensure_one()
        if not self.company_id.asset_journal_id:
            msg = _(
                'You do not have an asset journal configured for your company.\n Please, go to the asset configuration and select the asset journal.')
            action_id = self.env['ir.model.data'].get_object_reference(
                'l10n_cu_account_asset', 'action_asset_config_settings')[1]
            raise exceptions.RedirectWarning(msg, action_id, _('Go to the asset configuration panel'))

        return self.env.ref('l10n_cu_account_asset.action_view_l10n_cu_asset_change_account').read()

    @api.multi
    @api.constrains('name')
    def _check_category(self):
        '''
        Check if the category has registered assets may not be of type 'view'.
        @return: True or False
        '''
        self.ensure_one()
        asset_ids = self.env['account.asset.asset'].search([('category_id', '=', self.id),
                                                            ('state', 'in', ('open', 'idler'))])
        if self.internal_type == 'view' and asset_ids:
            raise ValidationError('The category have assets registered!')

    @api.onchange('company_id')
    def _onchange_company(self):
        self.account_depreciation_id = False
        self.account_asset_id = False

    @api.multi
    @api.onchange('internal_type', 'group_id')
    def on_change_internal_type(self):
        '''
        Function that controls changes in the internal type.
        @raise Warning: * If the category have at least one child category
        '''
        self.ensure_one()
        if self.child_ids:
            raise ValidationError(
                'You can not change the internal type if the category have at least one child category!')

    @api.multi
    @api.onchange('parent_id')
    def on_change_parent_id(self):
        '''
        Function that controls changes in the parent category.
        '''
        if self.parent_id:
            self.group_id = self.parent_id.group_id

    @api.multi
    @api.onchange('account_depreciation_id', 'account_asset_id')
    def on_change_account_depreciation(self):
        '''
        Function that controls the change in the depreciation/amortization account.
        @raise Warning: * If the depreciation/amortization account balance is different to 0
        '''
        self.ensure_one()
        # if (self.account_depreciation_id or self.account_asset_id) and self.asset_opening_done:
        if (self.account_depreciation_id and self.account_asset_id) and self.asset_opening_done:
            report_obj = self.env['report.account.report_trialbalance']
            account_depreciation_id_balance = report_obj._get_accounts(self.account_depreciation_id, 'all')[0][
                'balance']
            account_asset_id_balance = report_obj._get_accounts(self.account_asset_id, 'all')[0]['balance']

            # if not account_depreciation_id_balance:
            #     raise ValidationError(
            #         'You can not change manually the depreciation account if it has balance!')
            # if not account_asset_id_balance:
            #     raise ValidationError(
            #         'You can not change manually the depreciation account if it has balance!')
            for asset in self.asset_ids:
                if asset.state in ('open', 'idler', 'stop'):
                    raise ValidationError(
                        'You can not change manually the depreciation account if the category has assets in state open, idler or stop!')

    @api.onchange('account_asset_id')
    def onchange_account_asset(self):
        '''
        Function that controls the change in the asset account.
        @raise Warning: * If the asset account balance is different to 0
        '''
        for category in self:
            if category.account_asset_id and category.asset_opening_done:
                account_obj = self.env['account.account']
                report_obj = self.env['report.account.report_trialbalance']

                account = account_obj.browse(category.account_asset_id)
                account_balance = report_obj._get_accounts(account.id, 'all')[0]['balance']

                account_old = account_obj.browse(category.account_asset_id[0])
                account_old_balance = report_obj._get_accounts(account_old.id, 'all')[0]['balance']

                if not account_balance or not account_old_balance:
                    warning = {
                        'title': _('Warning!'),
                        'message': _('You can not change manually the asset account if it has balance!')
                    }
                    return {'warning': warning}
                for asset in category.asset_ids:
                    if asset.state in ('open', 'idler', 'stop'):
                        warning = {
                            'title': _('Warning!'),
                            'message': _(
                                'You can not change manually the asset account if the category has assets in state open, idler or stop!')
                        }
                        return {'warning': warning}

    @api.multi
    @api.onchange('depreciation_tax')
    def on_change_depreciation_tax(self):
        '''
        Function that controls the change in the depreciation tax.
        @raise Warning: * If the depreciation rate is smaller or equal than 0
        @raise Warning: * If the depreciation rate is greater than 100
        '''
        self.ensure_one()
        if self.depreciation_tax <= 0 or self.depreciation_tax > 100:
            raise ValidationError(
                'The depreciation rate should be between 0 and 100!')

        for asset in self.asset_ids:
            asset.depreciation_tax = self.depreciation_tax
            asset.compute_depreciation_board()

    @api.multi
    @api.onchange('group_id')
    def on_change_group(self):
        '''
        Function that controls changes in the group_id.
        @raise Warning: * If the category have at least one child category
        '''
        for cat in self:
            if cat.child_ids:
                warning = {'title': _('Warning!'),
                           'message': _(
                               'You can not change the groups if the category have at least one child category!')
                           }
                return {'warning': warning}

    @api.multi
    @api.onchange('method_progress_factor')
    def on_change_method_progress_factor(self):
        '''
        Function that controls the change in the degressive factor.
        @raise Warning: * If the degressive factor is smaller than 0
        '''
        self.ensure_one()
        if self.method_progress_factor <= 0:
            raise ValidationError('The degressive factor can not be smaller than 0!')

    @api.model
    def create(self, vals):
        '''
        Create a new record.
        '''
        if not vals.get('group_id', False):
            vals.update('group_id', vals['parent_id'] and self.browse(
                vals['parent_id']).group_id.id or None)
        return super(AccountAssetCategory, self).create(vals)

    @api.multi
    def unlink(self):
        '''
        Delete records with given ids.
        @raise Warning: * if there are assets with that category.
        '''
        for category_obj in self:
            if category_obj.asset_ids:
                raise exceptions.except_orm(_('Warning !'),
                                            _('You can not remove the assets category with asset assigned.'))

        return super(AccountAssetCategory, self).unlink()


class l10n_cu_ResponsableArea(models.Model):
    '''
    This is a class that saves all information relating to areas of responsibility for the assets.

    The important fields: \
        -- responsible: The field with name "Responsible" \
         is the relation many2one with class hr.employee for specify the \
         responsible of responsibility area.
        -- employee_ids:The field with name "List of Employees" \
         is the relation many2many with class hr.employee for specify the \
         list of employees in the area of responsibility.
        -- account_analytic_id: The field with name "Analytic account" \
         is the relation many2one with class account.analytic.account for specify the \
         analytic account used for the responsibility area.
         -- local_id: The field with name "Local" \
         is the relation many2one with class l10n_cu.local to specify the \
         local to which belongs the responsibility area.
    '''
    _name = "l10n_cu.resp.area"
    _description = "Assets, Area of responsibility"

    @api.multi
    @api.constrains('name', 'company_id')
    def _check_name(self):
        '''
        Verify that the name of the area of responsibility is not repeated in the company.
        '''
        if self.search([('name', '=', self.name), ('company_id', '=', self.company_id.id)], count=True) > 1:
            raise ValidationError('The name of the area of responsibility already exists in this company!')

    @api.multi
    @api.constrains('code', 'company_id')
    def _check_code(self):
        '''
        Verify that the name of the area of responsibility is not repeated in the company.
        '''
        if self.search([('code', '=', self.code), ('company_id', '=', self.company_id.id)], count=True) > 1:
            raise ValidationError('The code already exists in this company!')

    name = fields.Char('Name', required=True, help='Name of responsibility area')
    code = fields.Char('Code', required=True, help='Code of responsibility area')
    description = fields.Text('Description')
    unity = fields.Char('Countable Unit')
    responsible = fields.Many2one('hr.employee', 'Responsible', required=True)
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_resp_area_rel', 'resp_id', 'area_id',
                                    'List of Employees', required=False,
                                    help='List of employees of responsibility area')
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          domain="[('company_id', '=',company_id)]")
    # domain="[('account_ids', '=', account_depreciation_expense_id), ('company_id', '=',company_id)]")
    account_depreciation_expense_id = fields.Many2one('account.account', 'Depreciation expense account', required=True,
                                                      domain="[('company_id', '=',company_id)]")
    # , domain="[('internal_type', 'in', ('expense','process')), ('company_id', '=',company_id)]]")
    account_asset_asset_ids = fields.One2many('account.asset.asset', 'area', 'List of assets', readonly=True,
                                              domain=[('parent_id', '=', False)],
                                              help='List of assets of responsibility area')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('l10n_cu.resp.area'))
    analytical_restrictions = fields.Boolean('Analytical restrictions')
    number = fields.Char('Number')

    @api.multi
    def write(self, vals):
        if self.company_id.asset_opening_done:
            vals['number'] = self.env['ir.sequence'].get('asset_control_sequence')
        return super(l10n_cu_ResponsableArea, self).write(vals)

    @api.multi
    def print_control(self):
        return self.env.ref('l10n_cu_account_asset.report_l10n_cu_asset_control').report_action(self)

    @api.multi
    @api.onchange('account_depreciation_expense_id')
    def on_change_account_expense_depreciation_id(self):
        self.account_analytic_id = False

    @api.onchange('account_analytic_id')
    def on_change_account_analytic_id(self):
        '''
        Function that controls changes in the account_analytic_id.
        @raise Warning: * If the responsibility area have at least one asset
        '''
        if self.account_asset_asset_ids:
            warning = {
                'title': _('Warning!'),
                'message': _(
                    'You can not change the analytic account if the responsibility area has at least one asset!')
            }
            return {'warning': warning}

    @api.multi
    def unlink(self):
        '''
        Delete records with given ids.
        @raise Warning: * if the responsibility area contains assets.
        '''
        for area in self:
            if self.env['account.asset.asset'].search_count([('area', '=', area.id)]) > 1:
                raise exceptions.except_orm(_('Warning'),
                                            _('You cant not remove an area of responsibility that contains assets.'))
        return super(l10n_cu_ResponsableArea, self).unlink()


class l10n_cu_AdditionsReplacementsHistory(models.Model):
    """
    This class save the history data for parts of the machine will add or replace in theassets
    """
    _name = "l10n_cu.additions.replacements.history"

    asset_history_id = fields.Many2one('account.asset.history', 'History asset', ondelete='cascade')
    additions = fields.Char('Additions', required=True)
    replacements = fields.Char('Replacements', required=True)


class l10n_cu_AccountAssetsHistory(models.Model):
    _name = 'account.asset.history'
    _description = 'Asset history'
    _order = 'date desc, id desc'

    # campos del account.asset.history nativo de odoo 8
    name = fields.Char('History name')
    user_id = fields.Many2one('res.users', 'User', required=True)
    date = fields.Date(string='Date', default=date.today(), required=True)
    asset_id = fields.Many2one('account.asset.asset', string='Asset', required=True)
    method_time = fields.Selection(string='Time Method', required=True,
                                   selection=[('number', 'Number of Depreciations'), ('end', 'Ending Date')],
                                   help="The method to use to compute the dates and number of depreciation lines.\n"
                                        "Number of Depreciations: Fix the number of depreciation lines and the time between 2 depreciations.\n"
                                        "Ending Date: Choose the time between 2 depreciations and the date the depreciations won't go beyond."
                                   )
    method_number = fields.Integer(string='Number of Depreciations',
                                   help="The number of depreciations needed to depreciate your asset")
    # method_period = fields.Integer(string=u'Period Length',
    #                 help="Time in month between two depreciations")
    method_end = fields.Date(string='Ending date', default=fields.Date.context_today, )
    note = fields.Text(string='Note')
    # /campos del account.asset.history nativo de odoo 8

    date = fields.Date('Date', required=True)
    modification_type = fields.Selection([(1, 'Subledger data and/or category'),
                                          (2, 'Reevaluate'),
                                          (3, 'Depreciation data'),
                                          (4, 'Others'),
                                          (5, 'Initial'),
                                          (6, 'Asset Depreciation'),
                                          (7, 'Asset Movement'),
                                          (8, 'Depreciation Value')],
                                         'Modification type',
                                         help="Select the type of modification you desire realize.")
    category_id = fields.Many2one('account.asset.category', 'Asset category',
                                  help='Represent the category to belong the asset')
    previous_value = fields.Float('Previous Value')
    value = fields.Float('Gross Value')
    depreciated = fields.Boolean('Depreciated')
    paralyzed = fields.Boolean('Paralyzed')
    state = fields.Selection([('draft', 'Draft'), ('open', 'In use'), ('idler', 'Idler'), ('stop', 'Paralizado'),
                              ('close', 'Close')], 'State')
    method_period = fields.Selection([(1, 'Monthly'),
                                      (2, 'Bimonthly'),
                                      (3, 'Every three months'),
                                      (4, 'Every four months'),
                                      (6, 'Semestral'),
                                      (12, 'Annual')], 'Period length',
                                     help="Represents the estimated time in months between the depreciation of a period.")
    depreciation_tax = fields.Integer('Depreciation tax')
    method = fields.Selection([('linear', 'Linear'), ('degressive', 'Degressive')], 'Computation Method',
                              help="Choose the method to use to compute the amount of depreciation lines.\n"
                                   " * Linear: Calculated on basis of: Gross Value / Number of Depreciations\n"
                                   " * Degressive: Calculated on basis of: Residual Value * Degressive Factor")
    method_progress_factor = fields.Float('Degressive Factor')
    inventory_number = fields.Char("Inventory number")
    asset_name = fields.Char('Asset name')
    asset_category_group = fields.Char("Category group")
    purchase_date = fields.Date('Purchase date')
    transport_country = fields.Many2one('res.country', 'Country')
    equipment_type = fields.Many2one('l10n_cu.asset.machinery.type', 'Machinery type')
    transport_serial_number = fields.Char('Serial number')
    transport_chassis_number = fields.Char('Chassis number')
    transport_number_motor = fields.Char('Motor number')
    transport_power = fields.Float('Power')
    transport_model = fields.Char('Model')
    transport_mark = fields.Char('Mark')
    transport_tonnage = fields.Float('Tonnage')
    transport_manufacture_date = fields.Date('Manufacture date')
    transport_fuel_type = fields.Char('Fuel Type')
    transport_chapa = fields.Char('Plates')
    transport_add_ids = fields.One2many('l10n_cu.additions.replacements.history', 'asset_history_id',
                                        'Additons and replacements', help="Space for the biggest attaches and "
                                                                          "their possible substitutions")
    furniture_country = fields.Many2one('res.country', 'Country')
    furniture_type = fields.Many2one('l10n_cu.asset.furniture.type', 'Furniture type')
    furniture_serial_number = fields.Char('Serial Number')
    furniture_model = fields.Char('Model')
    furniture_mark = fields.Char('Mark')
    animals_purpose = fields.Char('Purpose')
    animals_identification = fields.Char('Identification number')
    expansions_modernizations = fields.Text('Expansions and modernizations')
    company_id = fields.Many2one('res.company', 'Company', required=False,
                                 default=lambda s: s.env['res.company']._company_default_get('account.asset.history'), )
    depreciation_value = fields.Float('Depreciation value', readonly=True)
    move_number = fields.Char('Move number', readonly=True)
    value_amount_depreciation = fields.Float('Amount Depreciation', readonly=True)
    active = fields.Boolean('Active', default=True)


# Fin Alian


# Eva

class l10n_cu_AssetsFurnitureType(models.Model):
    '''
    This class save the data from type of machinery which has the asset
    '''
    _name = "l10n_cu.asset.furniture.type"
    _description = "Type of furniture"

    name = fields.Char('Name', required=True, help='Name of the type of furniture.')
    description = fields.Text('Description')
    company_id = fields.Many2one('res.company', 'Company', required=False,
                                 default=lambda s: s.env['res.company']._company_default_get('account.asset.history'), )

    @api.multi
    @api.constrains('name')
    def _check_name(self):
        '''
        Verify that the name of the type furniture is not repeated in the company.
        '''
        if self.search([('name', '=', self.name), ('company_id', '=', self.company_id.id)], count=True) > 1:
            raise ValidationError('The furniture name already exists in this company!')


class l10n_cu_AssetsMachineryType(models.Model):
    '''
    This class save the data from type of machinery  which has the asset
    '''
    _name = "l10n_cu.asset.machinery.type"
    _description = "Machinery type"

    name = fields.Char('Name', required=True, help='Name of the type of machinery.')
    description = fields.Text('Description')
    company_id = fields.Many2one('res.company', 'Company', required=False,
                                 default=lambda s: s.env['res.company']._company_default_get('account.asset.history'), )

    @api.multi
    @api.constrains('name')
    def _check_name(self):
        '''
        Verify that the name of the type furniture is not repeated in the company.
        '''
        if self.search([('name', '=', self.name), ('company_id', '=', self.company_id.id)], count=True) > 1:
            raise ValidationError('The machinery name already exists in this company!')


class l10n_cu_AssetsTechnicalState(models.Model):
    """
    Class purpose:
        - Desoft solution to determine the technical state which has the assets

    Model Fields:
        - state: { type: (char), help: (State) }

        - description: { type: (text), help: (IDescription) }
    """
    _name = "l10n_cu.technical.state"
    _rec_name = 'state'

    state = fields.Char('State', help="Show the state that have the asset", required=True)
    description = fields.Text('Description')


class l10n_cu_AdditionsReplacements(models.Model):
    """
    This class save the data for parts of the machine will add or replace  in theassets
    """
    _name = "l10n_cu.additions.replacements"

    asset_id = fields.Many2one('account.asset.asset', 'Asset', ondelete='cascade')
    additions = fields.Char('Additions', required=True)
    replacements = fields.Char('Replacements', required=True)


class l10n_cu_AccountAssetAsset(models.Model):
    '''
    Solution of the Company 'Desoft' to extension the asset class through \
    the inheritance extension to the original class whit name account.asset.asset \
    developed in 'OpenERP'.Are added important attributes to correctly configure the assets.

    The important fields:
        -- area: Is the relation many2one with class l10n_cu.resp.area to identify \
        which area of responsibility the asset belongs.
        -- receiver_name : Is the relation many2one with class hr.employee to \
        identify the responsible asset inside the area of responsibility.
        -- inventory_number: Is a char field that allows to identify of the asset \
        with a unique code which is composed of the asset code and code of the \
        category to which the asset belongs.
        -- depreciation_tax: is a float field required to determine the asset \
        depreciation value which may be equal or not to the depreciation rate \
        of the asset category
        -- asset_control_ids: Is the relation one2many with class l10n_cu.asset.control \
        to save all the movements of assets that not accounted

    '''
    _name = "account.asset.asset"
    _description = "Asset Magnament"
    _inherit = 'account.asset.asset'

    @api.model
    def state_module_search(self, values=None, default=None):
        '''
         busca en un modulo, si uno de sus componente tiene el estado que se definio en la variable value.
         retornando dicho valor, de no estar retorna el valor definido en default
        '''
        for child in self.child_ids:
            if child.state in values:
                return child.state
        return default

    @api.model
    def get_module_area(self, asset_mod):
        var = asset_mod.child_ids.filtered(lambda a: a.state in ('open', 'idler', 'stop'))
        if var:
            return var[0].area.id
        return False

    @api.model
    def module_value(self, action='add'):
        '''
        define los valores de depreciacion del modulo o unidad funcional,
        si la action es add adiciona los valores de depreacion del componente al modulo
        si la action es rest se resta los valores de depreacion del componente al modulo
        '''
        operador = {'add': 1, 'rest': -1}
        asset_mod = self.parent_id
        area = asset_mod.get_module_area(asset_mod)
        vals = {'value': asset_mod.value + operador[action] * self.value,
                'area': area,
                'value_amount_depreciation': asset_mod.value_amount_depreciation + operador[
                    action] * self.value_amount_depreciation,
                'state': asset_mod.state_module_search(['open'], 'draft')}
        return self.write(vals)

    @api.multi
    def check_module_value(self, vals):
        res = {}
        for asset in self:
            # asset = self.browse(ids[0])
            if asset.state == 'open' and (asset.parent_id or vals.get('parent_id', False)):
                value = vals['value'] if vals.get('value', False) else asset.value
                if vals.get('parent_id', False):
                    if asset.parent_id:
                        self.module_value(asset.parent_id.id, asset.value, 'rest')
                    if vals['parent_id']:
                        self.module_value(vals['parent_id'], value)
                else:
                    self.module_value(asset.parent_id.id, value - asset.value)

    @api.multi
    def validate(self):
        if not self.depreciation_tax and not self.depreciated:
            raise exceptions.except_orm(_('Error !'),
                                        _(
                                            'The depreciation tax can not be equal than zero if the field not depreciate is not check'))
        if self.parent_id:
            self.module_value()
        self.write({'previous_state': 'open'})
        return super(l10n_cu_AccountAssetAsset, self).validate()

    @api.multi
    def set_to_draft(self):
        asset_id_draft = super(l10n_cu_AccountAssetAsset, self).set_to_draft()
        if asset_id_draft:
            if self.parent_id:
                self.module_value('rest')
            self.write({'previous_state': 'draft'})
        return asset_id_draft

    @api.multi
    def set_to_idler(self):
        if self.child_ids:
            if self.state_module_search(['draft'], 'idler') == 'draft':
                raise exceptions.except_orm('Error',
                                            "Un modulo no puede pasar a ocioso si tiene componente en estado borrador.\n")
        self.write({'state': 'idler', 'previous_state': 'idler'})

    @api.multi
    @api.depends('value', 'value_amount_depreciation')
    def _amount_residual(self):
        for asset in self:
            asset.value_residual = asset.value - asset.salvage_value - asset.value_amount_depreciation

    def _inverse_amount_residual(self):
        if not self.asset_opening_done:
            self.value_amount_depreciation = self.value - self.salvage_value - self.value_residual

    @api.multi
    def _get_method_number(self):
        res = {}
        for asset in self:
            res[asset.id] = round(
                (100 / float(asset.depreciation_tax)) * 12 / asset.method_period) if asset.depreciation_tax else 0
        return res

    @api.model
    def _create_depreciation_lin_obj(self, asset, i, amount, depreciation_date):
        depreciation_lin_obj = self.env['account.asset.depreciation.line']
        vals = {
            'amount': amount,
            'asset_id': asset.id,
            'sequence': i,
            'name': str(asset.id) + '/' + str(i),
            'remaining_value': asset.value_residual - amount,
            'depreciated_value': asset.value - asset.salvage_value - asset.value_residual,
            'depreciation_date': depreciation_date.strftime('%Y-%m-%d'),
        }
        obj = depreciation_lin_obj.create(vals)
        return obj

    @api.model
    def _depreciation_line(self, asset, posted_depreciation_line_ids, depreciation_date):
        mount_precision = self.env['decimal.precision'].precision_get('Account')
        i = len(posted_depreciation_line_ids)
        count_depreciation_year = 12 / asset.method_period
        depreciation_year = (asset.value * asset.depreciation_tax) / 100
        amount = round(depreciation_year / count_depreciation_year, mount_precision)

        date_last_period = (datetime(depreciation_date.year + 1, 1, 1) - relativedelta(months=asset.method_period))
        day_year_last_period = int(date_last_period.strftime('%j'))
        day_year_depreciation = int(depreciation_date.strftime('%j'))
        if day_year_depreciation >= day_year_last_period:
            amount_dif_rest = round(depreciation_year - amount * count_depreciation_year, mount_precision)
            amount = round(amount + amount_dif_rest, mount_precision)
        if asset.value_residual < amount:
            amount = round(asset.value_residual, mount_precision)
        #
        return self._create_depreciation_lin_obj(asset, i, amount, depreciation_date)

    @api.model
    def _depreciation_degressive(self, asset, posted_depreciation_line_ids, depreciation_date):
        mount_precision = self.env['decimal.precision'].precision_get('Account')
        i = len(posted_depreciation_line_ids)
        amount = round(asset.value_residual * asset.method_progress_factor, mount_precision)
        if amount == 0.0:
            amount = asset.value_residual
        # self._create_depreciation_lin_obj(asset, i, amount, depreciation_date)

        return self._create_depreciation_lin_obj(asset, i, amount, depreciation_date)

    @api.multi
    def delete_depreciation_board(self):
        depreciation_lin_obj = self.env['account.asset.depreciation.line']
        for asset in self:
            old_depreciation_line_ids = depreciation_lin_obj.search([('asset_id', '=', asset.id),
                                                                     ('state', '=', 'draft')])
            if old_depreciation_line_ids:
                old_depreciation_line_ids.unlink()

    @api.multi
    def compute_depreciation_board(self):
        depreciation_lin_obj = self.env['account.asset.depreciation.line']
        company = self.env.user.company_id
        for asset in self:
            if not company.asset_lock_date or asset.state == 'draft' or asset.value_residual == 0.0:
                continue
            asset.delete_depreciation_board()
            posted_depreciation_line = depreciation_lin_obj.search([('asset_id', '=', asset.id),
                                                                    ('state', '!=', 'draft')],
                                                                   order='depreciation_date desc', limit=1)
            if posted_depreciation_line:
                last_depreciation_date = datetime.strptime(posted_depreciation_line.depreciation_date, '%Y-%m-%d')
                depreciation_date = (last_depreciation_date + relativedelta(months=+asset.method_period))
            else:
                asset_lock_date = company.asset_lock_date
                depreciation_date = datetime.strptime(asset_lock_date, '%Y-%m-%d')
                if asset.subscribe_date > asset_lock_date:
                    depreciation_date = datetime.strptime(asset.subscribe_date, '%Y-%m-%d')
                depreciation_date += relativedelta(months=+asset.method_period)
            if asset.method == 'linear':
                self._depreciation_line(asset, posted_depreciation_line, depreciation_date)
            else:
                self._depreciation_degressive(asset, posted_depreciation_line, depreciation_date)
        return True

    @api.depends('move_ids')
    def _get_in_move(self):
        for move in self.move_ids:
            if move.state != 'draft':
                self.in_move = True

    category_id = fields.Many2one('account.asset.category', 'Asset category',
                                  required=False, change_default=True, readonly=True,
                                  states={'draft': [('readonly', False)], 'idler': [('readonly', True)]},
                                  domain="[('internal_type', '!=', 'view')]",
                                  help='Represent the category to belong the asset')
    asset_category_group = fields.Char("Category group", default='0')
    type2 = fields.Selection([('tangible', 'Tangible fixed asset'),
                              ('intangible', 'Intangible fixed asset'),
                              ('module', 'Control module'),
                              ('functional', 'Functional unit')], 'Type', required=True, default='tangible')
    inventory_number = fields.Char("Number of inventory", readonly=True, store=True,
                                   states={'open': [('readonly', False)]})
    area = fields.Many2one('l10n_cu.resp.area', 'Area of responsibility', readonly=True,
                           states={'open': [('readonly', False)]}, domain="[('company_id', '=', company_id)]")
    receiver_name = fields.Many2one('hr.employee', 'Receptor name', readonly=True, related='area.responsible')
    state = fields.Selection([('draft', 'Draft'), ('open', 'In use'), ('idler', 'Idler'),
                              ('stop', 'Paralizado'), ('close', 'Close')], 'State', required=True,
                             help="When an asset is created, the state is 'Draft'.\n "
                                  "If the asset is confirmed, the state goes in 'In use' and the depreciation lines "
                                  "can be posted in the accounting. You can manually close an asset when the "
                                  "depreciation is over. If the last line of depreciation is posted, the asset "
                                  "automatically goes in that state.")
    technical_state = fields.Many2one('l10n_cu.technical.state', 'Technical condition')
    depreciated = fields.Boolean('Not Depreciated', states={'draft': [('readonly', False)]})
    purchase_date = fields.Date('Purchase Date', help='Purchase date of the asset module')
    rented_asset = fields.Boolean('Rented', help="Indicates if the asset is rented.", default=False)
    asset_repair = fields.Boolean('Repair', help="Indicates if the asset is in repair.", default=False)
    depreciated_value = fields.Float('Value depreciated', readonly=True)
    method = fields.Selection([('linear', 'Linear'), ('degressive', 'Degressive')], 'Computation Method',
                              required=False, help="Method used to calculate the amount of the depreciation.")
    depreciation_tax = fields.Integer('Depreciation tax', states={'open': [('readonly', False)]})
    method_number = fields.Integer(compute=_get_method_number, string='Number of Depreciations', store=True,
                                   help="The number of depreciations needed to depreciate your asset")
    method_period = fields.Selection([(1, 'Monthly'), (2, 'Bimonthly'), (3, 'Every three months'),
                                      (4, 'Every four months'), (6, 'Semestral'), (12, 'Annual')], 'Period length',
                                     help="Represents the estimated time in months between the depreciation "
                                          "of a period.", default=1)
    history_ids = fields.One2many('account.asset.history', 'asset_id', 'History', readonly=True)
    transport_country = fields.Many2one('res.country', 'Country')
    transport_model = fields.Char('Model')
    equipment_type = fields.Many2one('l10n_cu.asset.machinery.type', 'Machinery type')
    transport_mark = fields.Char('Mark')
    transport_serial_number = fields.Char('Serial number')
    transport_tonnage = fields.Float('Tonnage')
    transport_chassis_number = fields.Char('Chassis number')
    transport_manufacture_date = fields.Date('Manufacture Date')
    transport_number_motor = fields.Char('Number Motor')
    transport_fuel_type = fields.Char('Fuel Type')
    transport_power = fields.Float('Power')
    transport_chapa = fields.Char('Plates')
    transport_add_ids = fields.One2many('l10n_cu.additions.replacements', 'asset_id', 'Additons and replacements',
                                        help='Space for the biggest attaches and their possible substitutions')
    furniture_country = fields.Many2one('res.country', 'Country')
    furniture_model = fields.Char('Model')
    furniture_type = fields.Many2one('l10n_cu.asset.furniture.type', 'Type of Furniture')
    furniture_mark = fields.Char('Mark')
    furniture_serial_number = fields.Char('Serial Number')

    animals_purpose = fields.Text('Purpose')
    animals_identification = fields.Char('Identification Number')

    expansions_modernizations = fields.Text('Expansions and modernizations')
    depreciation_line_ids = fields.One2many('account.asset.depreciation.line', 'asset_id', 'Depreciation Lines',
                                            readonly=True, states={'draft': [('readonly', False)],
                                                                   'open': [('readonly', False)]})

    parent_id = fields.Many2one('account.asset.asset', 'Control module/Functional unit', readonly=True,
                                states={'draft': [('readonly', False)]},
                                domain="[('type2', 'in', ('module','functional'))]", ondelete='cascade')
    child_ids = fields.One2many('account.asset.asset', 'parent_id', 'Children assets')
    sequence_id = fields.Many2one(related='category_id.sequence_id', string="Sequence Category")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    asset_opening_done = fields.Boolean('Asset Opening Done', related='company_id.asset_opening_done',
                                        default=lambda self: self.env.user.company_id.asset_opening_done)
    in_move = fields.Boolean(compute='_get_in_move', string='Is in move?')
    subscribe_date = fields.Date('Date of subscribe',
                                 default=lambda s: time.strftime('%Y-%m-%d') if not s.env[
                                     'res.company'].asset_opening_done else False)
    unsubscribe_date = fields.Date('Date of unsubscribe')
    partner_id = fields.Many2one('res.partner', 'Partner/Area', readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 help="name of the company or area that was rented or sent to repair the fixed asset.")
    move_ids = fields.Many2many('l10n_cu.asset.move', 'asset_move_account_asset_rel', 'asset_id', 'asset_move_id',
                                'Moves List')
    sub_ledger_number = fields.Char('Sub-Ledger Number', readonly=True)
    inventory_date = fields.Date('Date of last inventory', readonly=True)
    initial_value = fields.Float('Initial Value', readonly=True)
    final_value = fields.Float('Final Value', readonly=True)
    previous_state = fields.Char('Previous state', default='draft')
    has_been_paralyzed = fields.Boolean(default=False)
    value = fields.Float(string='Gross Value', required=True, readonly=True, digits=0, default=0,
                         states={'draft': [('readonly', False)]})
    value_residual = fields.Float(compute='_amount_residual', inverse='_inverse_amount_residual',
                                  digits=dp.get_precision('Account'), string='Residual Value', store=True)
    value_amount_depreciation = fields.Float('Amount Depreciation', readonly=True,
                                             states={'draft': [('readonly', False)]})

    _sql_constraints = [('serial_number_uniq', 'unique(company_id, inventory_number)',
                         'The inventory number already exists in the company!')]

    @api.multi
    def copy_data(self, default=None):
        if default is None:
            default = {}
        default['name'] = self.name + _(' (copy)')
        default['inventory_number'] = self.inventory_number + _(' (copy)')
        return super(l10n_cu_AccountAssetAsset, self).copy_data(default)

    @api.multi
    @api.constrains('value')
    def _check_value(self):
        for asset in self:
            if asset.type2 in ['tangible', 'intangible'] and asset.value <= 0:
                raise ValidationError(_('The gross value must be greater than 0!'))

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        return super(l10n_cu_AccountAssetAsset, self)._search(args, offset, limit, order, count, access_rights_uid)

    # @api.multi
    # def _get_asset_opening_done(self):
    #     for asset in self:
    #         asset.asset_opening_done = asset.company_id.asset_opening_done

    @api.multi
    def add_depreciation(self):
        # asset_obj = self.env['account.asset.asset']
        # asset = asset_obj.browse(ids[0])
        # context = context.copy()
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_cu.asset.add.depreciation',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {

            }
        }

    @api.multi
    def asset_add_components(self):
        '''
        Function that shows a wizard to add an asset to a control module/functional unit.
        @return: Returns the form view of the model 'l10n_cu.asset.add.components'.
        '''
        data_obj = self.env['ir.model.data']
        id2 = data_obj._get_id('l10n_cu_account_asset', 'view_l10n_cu_asset_add_components')
        if id2:
            id2 = data_obj.browse(id2[0]).res_id
        context = self.env.context
        if context.get('type2') == 'module':
            context.update({'grs': [2, 3, 4]})
        else:
            context.update({'grs': [1, 2, 3, 4, 7]})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(id2, 'form')],
            'res_model': 'l10n_cu.asset.add.components',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context
        }

    @api.multi
    def sub_ledger_asset_countable(self):
        data_obj = self.env['ir.model.data']
        compose_form_id = data_obj.get_object_reference(
            'l10n_cu_account_asset', 'l10n_cu_sub_ledger_countable_assistant_form')[1]
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(compose_form_id, 'form')],
            'res_model': 'l10n_cu_account_asset.sub.ledger.countable.assistant',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_asset_id': self.id}
        }

    @api.multi
    def sub_ledger_asset(self):
        if self.asset_category_group == '1':
            return self.env.ref(
                'l10n_cu_account_asset.report_l10n_cu_sub_ledger_building_construct_report').report_action(self)
        elif self.asset_category_group in ('2', '7'):
            return self.env.ref(
                'l10n_cu_account_asset.report_l10n_cu_sub_ledger_furniture_others_report').report_action(self)
        elif self.asset_category_group in ('3', '4'):
            return self.env.ref(
                'l10n_cu_account_asset.report_l10n_cu_sub_ledger_machinery_in_general_report').report_action(self)
        elif self.asset_category_group == '5':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_sub_ledger_permanent_plant_report').report_action(
                self)
        elif self.asset_category_group == '8':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_sub_ledger_general_report').report_action(self)
        elif self.asset_category_group == '6':
            return self.env.ref('l10n_cu_account_asset.report_l10n_cu_sub_ledger_animals_report').report_action(self)
        else:
            return True

    @api.multi
    def asset_return(self):
        '''
        Function that shows a wizard to return a rented/repaired asset.
        @return: Returns the form view of the model 'l10n_cu.asset.return.asset'.
        '''
        data_obj = self.env['ir.model.data']
        id2 = data_obj._get_id('l10n_cu_account_asset',
                               'view_l10n_cu_asset_return_asset')
        if id2:
            id2 = data_obj.browse(id2).res_id
        context = self.env.context

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(id2, 'form')],
            'res_model': 'l10n_cu.asset.return.asset',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context
        }

    @api.multi
    def modify_info(self):
        '''
        Function that shows a wizard to modify the asset information.
        @return: Returns the form view of the model 'l10n_cu.asset.modify.info'.
        '''
        data_obj = self.env['ir.model.data']
        id2 = data_obj._get_id('l10n_cu_account_asset',
                               'view_l10n_cu_asset_modify_info')
        if id2:
            id2 = data_obj.browse(id2).res_id
        context = self.env.context

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_cu.asset.modify.info',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(id2, 'form')],
            'target': 'new',
            'context': context,
        }

    @api.onchange('type2', 'company_id')
    def onchange_type(self):
        res = {'value': {'category_id': None, 'parent_id': None}}
        if self.type2 == 'intangible':
            category_group_code = ['8']
        elif self.type2 in ('tangible', 'functional'):
            category_group_code = ['1', '2', '3', '4', '5', '6', '7']
        elif self.type2 == 'module':
            category_group_code = ['2', '3', '4']
        else:
            category_group_code = ['1', '2', '3', '4', '5', '6', '7', '8']

        group_ids = self.env['l10n_cu.asset.category.group'].search([('code', 'in', category_group_code)]).ids

        domain = [('group_id', 'in', group_ids), ('company_id', '=', self.company_id.id)]
        if self.type2 in ('module', 'functional'):
            if self.type2 == 'module':
                domain.append(('register_module', '=', True))
            else:
                domain.append(('register_functional_basic_unit', '=', True))
            self.value = 0
        res['domain'] = {'category_id': domain}
        if self.type2:
            category_ids = self.env['account.asset.category'].search(domain, limit=1)
            self.category_id = category_ids and category_ids or None
        return res

    @api.multi
    @api.onchange('category_id', 'parent_id')
    def onchange_category_id(self):
        if self.category_id:
            self.asset_category_group = self.category_id.group_id.code
            self.sequence_id = self.category_id.sequence_id.id if self.category_id.sequence_id else None
            if not self.parent_id:
                self.inventory_number = False
                self.depreciated = self.category_id.not_depreciate
                self.method = self.category_id.method
                self.depreciation_tax = self.category_id.depreciation_tax
                self.method_period = int(self.category_id.method_period)
                self.method_progress_factor = self.category_id.method_progress_factor

    @api.model
    def consec(self, list_cons):
        last_number = 1
        ids = self.search([('inventory_number', 'like', list_cons + '.')])
        if ids:
            assets = ids.read(['inventory_number'])
            last_number = max([int(el['inventory_number'].split('.')[-1]) for el in assets]) + 1
        return list_cons + '.' + str(last_number)

    @api.multi
    @api.onchange('parent_id', 'category_id')
    def onchange_parent_id(self):
        if self.parent_id and self.parent_id.inventory_number:
            self.inventory_number = self.consec(self.parent_id.inventory_number)
            self.method = self.parent_id.method
            self.depreciation_tax = self.parent_id.depreciation_tax
            self.method_period = self.parent_id.method_period
            self.method_progress_factor = self.parent_id.method_progress_factor
            self.depreciated = self.parent_id.depreciated
            self.area = self.parent_id.area
        else:
            self.area = False
            self.inventory_number = False
            self.depreciated = False
            if self.category_id:
                self.method = self.category_id.method
                self.depreciation_tax = self.category_id.depreciation_tax
                self.method_period = int(self.category_id.method_period)
                self.method_progress_factor = self.category_id.method_progress_factor
            else:
                self.method = False
                self.depreciation_tax = False
                self.method_period = False
                self.method_progress_factor = False

    def get_value_residual(self, value, salvage_value, value_amount_depreciation):
        return (value - salvage_value) - value_amount_depreciation

    @api.multi
    @api.onchange('value', 'value_amount_depreciation', 'salvage_value')
    def onchange_purchase(self):
        if self.value_amount_depreciation > self.value:
            self.value = False
            raise UserError(_('The value of accumulated depreciation can not be greater than the gross '
                              'value of the asset.'))

    @api.multi
    @api.onchange('depreciated')
    def onchange_depreciated(self):
        if self.depreciated:
            self.salvage_value = self.value
            self.value_residual = 0
        else:
            self.salvage_value = 0
            # self.value_residual = self.get_value_residual(
            #     self.value, self.salvage_value, self.value_amount_depreciation)

    @api.multi
    @api.onchange('method', 'depreciation_tax', 'category_id')
    def onchange_depreciation_tax(self):
        if self.method == 'linear' and (self.depreciation_tax <= 0.0 or self.depreciation_tax > 100):
            self.depreciation_tax = self.category_id and self.category_id.depreciation_tax or 0.0
            raise ValueError('The depreciation rate can not be smaller than 0 or greater than to 100!')

    @api.multi
    @api.onchange('method', 'method_progress_factor', 'category_id')
    def onchange_method_progress_factor(self):
        res = {'value': {}}
        if self.method == 'degressive' and self.method_progress_factor <= 0.0:
            self.method_progress_factor = self.category_id and self.category_id.method_progress_factor or 0.0
            raise ValueError(_('The degressive factor can not be smaller than 0!'))

    @api.multi
    def write(self, vals):
        if not vals.get('active'):
            return super(l10n_cu_AccountAssetAsset, self).write(vals)
        else:
            self.ensure_one()
            if vals.get('subscribe_date', False):
                if vals.get('purchase_date', False):
                    if vals['subscribe_date'] < vals['purchase_date']:
                        raise exceptions.except_orm(_('Error !'), (
                            _('The subscribe date (%s) can not be lower than the purchase date (%s)')) % (
                                                        vals['subscribe_date'], self.purchase_date))
                elif self.purchase_date and vals['subscribe_date'] < self.purchase_date:
                    raise exceptions.except_orm(_('Error !'), (
                        _('The subscribe date (%s) can not be lower than the purchase date (%s)')) % (
                                                    vals['subscribe_date'], self.purchase_date))
                if vals['subscribe_date'] > time.strftime('%Y-%m-%d'):
                    raise exceptions.except_orm(_('Error !'), (
                        _('The subscribe date (%s) can not be greater than the current date (%s)')) %
                                                (vals['subscribe_date'], time.strftime('%Y-%m-%d')))
            if vals.get('inventory_number', False):
                if self.child_ids:
                    query = "update account_asset_asset set inventory_number = REPLACE(inventory_number, %s, %s) where id in %s"
                    childs_ids = tuple([el.id for el in self.child_ids])
                    self.env.cr.execute(query, (self.inventory_number, self.inventory_number, childs_ids))
            # if asset.state != 'draft' and asset.asset_opening_done:
            #     vals['sub_ledger_number'] = self.env['ir.sequence'].get('sub.ledger.seq')
            result = super(l10n_cu_AccountAssetAsset, self).write(vals)
            valschild = {item: vals[item] for item in ASSET_DEP_ARGS if vals.get(item, None) is not None}
            if valschild and self.child_ids:
                for ch in self.child_ids:
                    ch.write(valschild)
            return result

    @api.multi
    def unlink(self):
        for asset in self:
            if asset.state != 'draft':
                raise exceptions.except_orm(_('Error !'), _('Can not delete your assets once confirmed high.'))
        return super(l10n_cu_AccountAssetAsset, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('subscribe_date', False) and vals.get('purchase_date', False):
            if vals['subscribe_date'] < vals['purchase_date']:
                raise exceptions.except_orm(_('Error !'),
                                            (_(
                                                'The subscribe date (%s) can not be lower than the purchase date (%s)')) %
                                            (vals['subscribe_date'], vals['purchase_date']))
            if vals['subscribe_date'] > time.strftime('%Y-%m-%d'):
                raise exceptions.except_orm(_('Error !'),
                                            (_(
                                                'The subscribe date (%s) can not be greater than the current date (%s)')) %
                                            (vals['subscribe_date'], time.strftime('%Y-%m-%d')))
        # vals['sub_ledger_number'] = self.env['ir.sequence'].get('sub.ledger.seq')
        asset_id = super(l10n_cu_AccountAssetAsset, self).create(vals)
        return asset_id

    @api.multi
    def _compute_entries(self, date, group_entries=False):
        depreciation_ids = self.env['account.asset.depreciation.line'].search([
            ('asset_id', 'in', self.ids), ('depreciation_date', '<=', date),
            ('move_check', '=', False)])
        if group_entries:
            return depreciation_ids.create_grouped_move()

        return depreciation_ids.create_move(self.depreciation_line_ids)
