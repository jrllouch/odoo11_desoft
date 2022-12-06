# -*- coding: utf-8 -*-
import time
from datetime import datetime, date
from odoo import models, fields, exceptions, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons import decimal_precision as dp
from lxml import etree

from odoo.tools import float_compare


class l10n_cuTechnicalState(models.Model):
    """
    Class purpose:
        - Desoft solution to determine the technical state which has the assets

    Model Fields:
        - state: { type: (char), help: (State) }

        - description: { type: (text), help: (IDescription) }
    """
    _name = "l10n_cu.technical.state"
    _rec_name = 'state'

    state = fields.Char(
        'State', help='Show the state that have the asset', size=30, required=True)
    description = fields.Text('Description')


class l10n_cu_AssetMoveCategory(models.Model):
    """
    Class purpose:
        - Desoft solution to determine the different movements that are made to assets

    Model Fields:
        - name: { type: (char), help: (Operation type) }

        - code: { type: (char), help: (Code) }

        - groups: { type: (selecction), values: (Alta, Baja, Ninguno), help: (Groups) }


    """
    _name = "l10n_cu.asset.move.category"
    _description = "Operation Type"

    name = fields.Char('Operation type', size=255,
                       required=True, translate=True)
    code = fields.Char('Code', size=30, required=True)
    groups = fields.Selection(
        [('alta', 'Alta'), ('baja', 'Baja'), ('ninguno', 'Ninguno')], 'Groups')


class l10n_cu_AssetMove(models.Model):
    """
    Class purpose:
        - Desoft solution to save all information related to the movement of assets

    Model Fields:
        - company: { type: (char), help: (Entity) }
        - company_code: { type: (char), help: (Company code) }
        - address: { type: (text), help: (Address) }
        - asset_move_category_id: { type: (many2one), help: (Operation type),}
        - asset_move_category_code: { type: (char), help: (Operation code) }
        - account_asset_asset_id: { type: (many2one), help: (Asset) }
        - description: { type: (text), help: (Description asset) }
        - date: { type: (date), help: (Operation date) }
        - depreciation_date: { type: (date), help: (Depreciation date) }
        - accumulated_depreciation_amount: { type: (float), help: (Depreciation amount) }
        - sale_amount: { type: (float), help: (Sale price) }
        - valuation_amount: { type: (float), help: (Valuation amount) }
        - asset_move_resource: { type: (many2one), help: (Resource) }
        - receiver_name: { type: (many2one), help: (Receptor name) }
        - reception_date: { type: (date), help: (Date of reception) }
        - technical_id: { type: (many2one), help: (Technician) }
        - technical_charge: { type: (char), help: (Charge of Technician) }
        - area: { type: (char), help: (Area of responsibility) }
        - reception_area: { type: (many2one), help: (Area receptora) }
        - tec_state: { type: (many2one), help: (State technical asset) }
        - who_elaborate_model: { type: (char), help: (Elaborated by) }
        - who_approve_model: { type: (many2one), help: (terminated by) }
        - who_approve_model_charge: { type: (char), help: (Charge of to who it approves) }
        - authorization_date: { type: (date), help: (Authorization date) }
        - who_score_registration: { type: (many2one), help: (Entered by) }
        - emission_date: { type: (date), help: (Emission date) }
        - emission_number: { type: (char), help: (Number of model) }
        - proof_number: { type: (integer), help: (Number of the voucher) }
        - proof_date: { type: (date), help: (Dates of the voucher) }
        - move_description: { type: (text), help: (Description of the movement) }
        - state:  { type: (selection), help: (State), values: (Draft, terminated, Confirmed, Canceled) }
        - account_move_ids: { type: (one2many), help: (Account move entry) }
        - move_group_type: { type: (selection), help: (Move Group Type) }
        - company_id: { type: (many2one), help: (Company to receive the asset) }
        - predecessor_move_id: { type: (many2one), help: (Predecessor) }
        - revert_move: { type: (boolean), help: (Revert) }
        - last_account_move: { type: (many2one), help: (Last account move) }
        - module_move: { type: (boolean), help: (Module move) }
        - asset_module_id: { type: (many2one), help: (Asset module) }
        - is_linking_module: { type: (boolean), help: (Is created by Link the Asset to Module) }
        - partner_id: { type: (many2one), help: (Partner) }
        - move_category_domain: { type: (function)}
        - move_confirmed: { type: (function)}

    Restrictions:
        - _check_valuation_amount: (This function checks that the value of avaluo is not equal to 0)
        - _check_valuation_amount: (This function checks if a movement is high by restructuration \
                                    the accumulated depreciation is not less than the value of assets)
        - _check_accumulated_depreciation_zero: (This function checks if a movement is high by restructuration \
                                                the accumulated depreciation is not less or equal to 0)

    Related Views:
        - view_asset_move_form: {type : (form) }

        - view_asset_move_tree: {type : (tree) }

        - view_asset_move_search: {type : (search)}


    """
    _name = "l10n_cu.asset.move"
    _description = "Asset Move"
    _rec_name = 'number'

    @api.multi
    def get_account_counterpart(self):
        if self.asset_move_category_code == '01' and self.company_id.account_purchase_id:
            return self.company_id.account_purchase_id.id
        if self.asset_move_category_code == '02' and self.company_id.account_purchase_id:
            return self.company_id.account_purchase_id.id
        if self.asset_move_category_code == '03' and self.company_id.account_investments_id:
            return self.company_id.account_investments_id.id
        if self.asset_move_category_code == '05' and self.company_id.account_adjustment_missing_id:
            return self.company_id.account_adjustment_missing_id.id
        if self.asset_move_category_code == '06' and self.company_id.account_adjustment_loss_id:
            return self.company_id.account_adjustment_loss_id.id
        if self.asset_move_category_code == '07' and self.company_id.account_adjustment_surplus_id:
            return self.company_id.account_adjustment_surplus_id.id
        if self.asset_move_category_code == '12' and self.company_id.account_adjustment_loss_id:
            return self.company_id.account_adjustment_loss_id.id
        return False

    number = fields.Char('Number', readonly=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('terminated', 'Terminated'),
                              ('canceled', 'Canceled')], 'State', default='draft')
    date = fields.Date('Document Date', help='Document date', required=True)
    asset_move_category_id = fields.Many2one('l10n_cu.asset.move.category', "Operation type", required=True,
                                             domain="[('code', 'not in',('24','26','28','29'))]")
    asset_move_category_code = fields.Char(
        'Code', related='asset_move_category_id.code', readonly=True, store=True)
    partner_id = fields.Many2one('res.partner', 'Partner')
    partner_name = fields.Char('Partner', size=255, readonly=True)
    area_id = fields.Many2one('l10n_cu.resp.area', 'Origin Area')
    area = fields.Char('Origin Area', related='area_id.name', readonly=True, store=True)
    reception_area = fields.Many2one('l10n_cu.resp.area', 'Receiving Area')
    reception_area_name = fields.Char(
        'Receiving Area', related='reception_area.name', readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Receptor', readonly=True)
    account_id = fields.Many2one('account.account', 'Counterpart Account')
    domain_state = fields.Char('Domain State')
    domain_state1 = fields.Char('Domain State 1')
    domain_state2 = fields.Char('Domain State 2')
    asset_ids = fields.Many2many('account.asset.asset', 'asset_move_account_asset_rel', 'asset_move_id', 'asset_id',
                                 'Assets List', required=True,
                                 domain="['|',('state', '=', domain_state),"
                                        " '|',('state', '=', domain_state1),"
                                        "     ('state', '=', domain_state2),"
                                        "     ('area', '=', area_id),"
                                        "     ('type2', 'in', ('tangible', 'intangible')),"
                                        "     ('rented_asset', '=', False),"
                                        "     ('asset_repair', '=', False)]")
    asset_move_history_ids = fields.One2many('l10n_cu.asset.move.history', 'asset_move_id', 'Assets List',
                                             readonly=True)
    technical_id = fields.Many2one('hr.employee', 'Technician')
    technical_charge = fields.Char('Charge of Technician', size=255)
    move_description = fields.Text(
        'Note', required=True, help='Description of the movement')
    approved_by = fields.Many2one('hr.employee', 'Approved by')
    elaborated_by = fields.Many2one(
        'hr.employee', 'Elaborated by', required=True)
    entered_by = fields.Many2one('res.users', 'Entered by', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', help="Company to receive the asset.",
                                 default=lambda self: self.env.user.company_id.id)
    operation_date = fields.Date('Operation Date')
    approval_date = fields.Date('Approval Date')
    is_account = fields.Boolean('Is Account', readonly=True, default=True)
    area_readonly = fields.Boolean('Has component?', default=False)
    # 'area_readonly': fields.Function(_get_area_readonly, string='Has component?', type='boolean'),
    return_date = fields.Date('Return Date', readonly=True)
    account_move_id = fields.Many2one(
        'account.move', 'Account move', readonly=True)

    _sql_constraints = [('number_unique', 'unique(number)',
                         'The number of the movement must be unique!')]

    @api.model
    def create(self, vals):
        if not self.env.user.company_id.asset_opening_done:
            raise exceptions.except_orm(_('Error !'),
                                        _('You can not create a movement with the initial loading open.'))
        vals['operation_date'] = vals['date']
        return super(l10n_cu_AssetMove, self).create(vals)

    @api.multi
    def unlink(self):
        for move in self:
            if move.state != 'draft':
                raise exceptions.except_orm(_('Error !'), _(
                    'Can not delete movements in state different of draft.'))
        return super(l10n_cu_AssetMove, self).unlink()

    @api.multi
    @api.onchange('asset_move_category_id')
    def onchange_asset_move_category(self):
        if self.asset_move_category_id:
            # self.asset_move_category_code = self.asset_move_category_id.code
            if self.asset_move_category_id.code in ('01', '02', '07'):
                self.domain_state = 'draft'
                self.domain_state1 = 'draft'
                self.domain_state2 = 'draft'
                self.area_id = False
                # self.area = False
                self.asset_ids = False
            else:
                self.domain_state = False
                self.domain_state1 = False
                self.domain_state2 = False
                self.area_id = False
                # self.area = False
                self.asset_ids = False
        else:
            self.asset_ids = [(5, 0, 0)]

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner(self):
        if self.partner_id:
            self.partner_name = self.partner_id.name

    @api.multi
    @api.onchange('asset_ids')
    def onchange_asset_ids(self):
        if self.asset_ids:
            parents = {}
            for asset in self.asset_ids:
                if asset.parent_id and asset.parent_id.state in ('open', 'idler', 'stop'):
                    parent = parents.setdefault(
                        asset.parent_id.id, {'asset': asset, 'area': asset.parent_id.area})
                    area = parent['area']
                    asset1 = parent['asset']
            if parents:
                for parent, values in parents.items():
                    if area.id != values['area'].id:
                        self.area_readonly = False
                        self.asset_ids = []
                        raise ValidationError('In the list of asset there are components (%s - %s) that have '
                                              'associated with modules of different areas (%s - %s). Select components '
                                              'with parent in the same area.') % (
                                  asset1.name, values['asset'].name, area.name, values['area'].name)

                self.reception_area = area.id
                # self.reception_area_name = area.name
                self.employee_id = area.responsible.id
                self.area_readonly = True
            else:
                self.area_readonly = False

    @api.multi
    @api.onchange('area_id')
    def onchange_area(self):
        if self.area_id:
            # self.area = self.area_id.name
            if self.asset_move_category_code == '08':
                self.domain_state = 'open'
                self.domain_state1 = 'open'
                self.domain_state2 = 'open'
            elif self.asset_move_category_code == '09':
                self.domain_state = 'idler'
                self.domain_state1 = 'idler'
                self.domain_state2 = 'idler'
            elif self.asset_move_category_code in ('10', '11'):
                self.domain_state = 'open'
                self.domain_state1 = 'idler'
                self.domain_state2 = 'idler'
            elif self.asset_move_category_code not in ('01', '02'):
                self.domain_state = 'open'
                self.domain_state1 = 'idler'
                self.domain_state2 = 'stop'
            self.asset_ids = False

    @api.multi
    @api.onchange('reception_area')
    def onchange_reception_area(self):
        if self.reception_area:
            self.reception_area_name = self.reception_area.name
            self.employee_id = self.reception_area.responsible.id

    @api.multi
    def confirmed(self):

        self.ensure_one()
        company = self.env.user.company_id
        # current_period = self.env['account.period.module']._get_active_period('l10n_cu_asset', company.id)
        # date_start = current_period.period_id.date_start
        # date_stop = current_period.period_id.date_stop
        date_stop = company.asset_lock_date

        # if self.date < date_start or self.date > date_stop:
        if self.date < date_stop:
            raise exceptions.except_orm(_('Error !'),
                                        # _('The document date (%s) must be in the current period (%s - %s)')
                                        _('The document date (%s) must be later than %s')
                                        % (self.date, date_stop))

        for asset in self.asset_ids:
            if self.search([('state', '=', 'confirmed'), ('asset_ids', 'in', asset.id), ('id', '!=', self.id)]):
                raise exceptions.except_orm(_('Error !'),
                                            _('The movement can not be confirmed because one of its assets is in other '
                                              'movement that is not confirmed'))
        number = self.env['ir.sequence'].get('move_asset_sequence')

        # module_l10n_cu_asset_inventory not found ¿?

        # config_obj = self.env['res.config.settings']

        # inv_id = config_obj.search([('company_id', '=', company.id)])

        # if inv_id.module_l10n_cu_asset_inventory:
        #     if self.asset_inventory_move_id:
        #         line_obj = self.env['l10n_cu.asset.inventory.line']
        #         # ('inventory_id', '=', self.asset_inventory_move_id.id),
        #         line = line_obj.search([('asset_id', '=', self.asset_ids[0].id)])
        #         if line:
        #             note = line.note and line.note or ''
        #             line.write({'note': note + ' No del documento generado: ' + number})

        history_ids = []

        for asset in self.asset_ids:
            history_ids.append((0, 0, {
                'asset_move_id': self.id,
                'name': asset.name,
                'inventory_number': asset.inventory_number,
                'value_amount_depreciation': asset.value_amount_depreciation,
                'value': asset.value,
                'subscribe_date': asset.subscribe_date,
            }))

        return self.write({'state': 'confirmed',
                           'number': number,
                           'asset_move_history_ids': history_ids,
                           'account_id': self.get_account_counterpart()})

    @api.multi
    def terminated(self):
        self.ensure_one()
        if not self.company_id.asset_opening_done:
            raise exceptions.except_orm(_('Warning !'),
                                        _('You can not change the movement to terminated state while the '
                                          'initial load is open.'))
        company = self.env.user.company_id
        date_stop = company.asset_lock_date

        if self:
            if self.date > self.approval_date:
                raise exceptions.except_orm(_('Warning !'), _('The document date (%s) can not be greater than the '
                                                              'approval date (%s).') % (self.date, self.approval_date))
            if self.approval_date <= date_stop:
                raise exceptions.except_orm(_('Error !'), _('The approval date (%s) must be later than '
                                                            '%s') % (self.approval_date, date_stop))
            if self.asset_move_category_code in ('01', '02', '03', '05', '06', '07', '12'):
                self.is_account = True
                return self.operation_account()
            if self.asset_move_category_code in ('04', '08', '09', '10', '11'):
                self.is_account = False
                return self.operation_no_account(self.asset_move_category_code)

    @api.multi
    def canceled(self):
        self.ensure_one()
        if self.state != 'terminated':
            return self.write({'state': 'canceled'})
        # if self.asset_move_category_code in ('04', '08', '09', '10', '11'):
        #     #        OJOOOOO validar que se esta cancelando el ultimo movimiento asociado al activo
        #     for asset in self.asset_ids:
        #         if self.asset_move_category_code == '04':
        #             asset.write({'area': self.area_id.id})
        #         elif self.asset_move_category_code == '08':
        #             asset.write({'state': 'open'})
        #         elif self.asset_move_category_code == '09':
        #             asset.set_to_idler()
        #         elif self.asset_move_category_code == '10':
        #             data = {'rented_asset': False}
        #             if self.partner_id:
        #                 data.update({'partner_id': False})
        #             asset.write(data)
        #         elif self.asset_move_category_code == '11':
        #             data = {'asset_repair': False}
        #             if self.partner_id:
        #                 data.update({'partner_id': False})
        #             asset.write(data)
        #     employee = self.env['hr.employee'].search(
        #         [('user_id', '=', self.env.user.id)], limit=1)
        #     return self.write({'state': 'canceled', 'entered_by': employee.id})
        # if self.asset_move_category_code in ('01', '02', '03', '05', '06', '07', '12'):
        #     asset_account_move = self.env['l10n_cu.asset.account.move']
        #     journal_item_aux_obj = self.env['journal.item.aux']
        #     values = {}
        #     if self.asset_move_category_code == '01':
        #         values = {
        #             'name': _('Canceling movement of high ') + self.number,
        #             'asset_move_category_code': self.asset_move_category_code,
        #         }
        #     if self.asset_move_category_code == '02':
        #         values = {
        #             'name': _('Canceling movement of purchase ') + self.number,
        #             'asset_move_category_code': self.asset_move_category_code,
        #         }
        #     if self.asset_move_category_code == '03':
        #         values = {
        #             'name': _('Canceling movement of sale ') + self.number,
        #             'asset_move_category_code': self.asset_move_category_code,
        #         }
        #     if self.asset_move_category_code == '05':
        #         values = {
        #             'name': _('Canceling movement of missing adjustment ') + self.number,
        #             'asset_move_category_code': self.asset_move_category_code,
        #         }
        #     if self.asset_move_category_code == '06':
        #         values = {
        #             'name': _('Canceling movement of loss adjustment ') + self.number,
        #             'asset_move_category_code': self.asset_move_category_code,
        #         }
        #     if self.asset_move_category_code == '07':
        #         values = {
        #             'name': _('Canceling movement of surplus adjustment ') + self.number,
        #             'asset_move_category_code': self.asset_move_category_code,
        #         }
        #     if self.asset_move_category_code == '12':
        #         values = {
        #             'name': _('Canceling movement of low ') + self.number,
        #             'asset_move_category_code': self.asset_move_category_code,
        #         }
        #     values.update({'internal_type': 'cancel'})
        #     res = asset_account_move.create(values)
        #
        #     move_obj = self.env['account.move']
        #     move = move_obj.search([('ref', '=', self.number)], limit=1)
        #     for line in move.line_id:
        #         journal_item_aux_obj.create({
        #             'name': line.name,
        #             'ref': self.number,
        #             'asset_account_move_id': res.id,
        #             'account_id': line.account_id.id,
        #             'credit': line.debit,
        #             'debit': line.credit})
        #
        #     return {
        #         'name': "Generating Account Move",
        #         'view_type': 'form',
        #         'view_mode': 'form',
        #         'res_id': res.id,
        #         'res_model': 'l10n_cu.asset.account.move',
        #         'type': 'ir.actions.act_window',
        #         'target': 'new',
        #         'context': self.env.context
        #     }

    @api.multi
    def print_report(self):
        return self.env.ref('l10n_cu_account_asset.report_l10n_cu_asset_move_report').report_action(self)

    @api.multi
    def operation_account(self):
        self.ensure_one()
        created_moves = self.env['account.move']
        if not self.company_id.asset_journal_id:
            model_obj = self.env['ir.model.data']
            msg = _('You do not have an asset journal configured for your company.\n Please, go to the asset '
                    'configuration and select the asset journal.')
            model, action_id = model_obj.get_object_reference(
                'l10n_cu_account_asset', 'action_asset_config_settings')
            raise exceptions.RedirectWarning(
                msg, action_id, _('Go to the asset configuration panel'))
        if not self.account_id:
            raise exceptions.except_orm(_('Error !'),
                                        _(
                                            'You can not terminate the movement without configure a counterpart account.'))
        for asset in self.asset_ids:
            if self.asset_move_category_code in ('01', '02', '07'):
                if not asset.depreciation_tax and not asset.depreciated:
                    raise exceptions.except_orm(_('Error !'), _('The depreciation tax of the asset (%s) can not be '
                                                                'equal than zero if the field not depreciate is not '
                                                                'check') % asset.name)
            if not asset.category_id.account_asset_id:
                raise exceptions.ValidationError(_('You do not have an asset account configured for the category %s.')
                                                 % asset.category_id.name)
            if not asset.category_id.account_depreciation_id:
                raise exceptions.ValidationError(_('You do not have a depreciation account configured for the '
                                                   'category %s.') % asset.category_id.name)
        account_move = self._prepare_account_move()

        lines = []
        nature = self.asset_move_category_code in (
            '01', '02', '07') and 'debit' or 'credit'
        accounts = self._get_account_values(self, nature)
        company_currency = self.company_id.currency_id.id
        current_currency = self.company_id.asset_journal_id.currency_id
        currency = company_currency != current_currency and current_currency or False
        context = dict(self.env.context)
        context.update({'date': self.operation_date})

        total_amount = 0.00
        total_depreciation = 0.00
        total_amount_currency = 0.00
        for account_id, values in accounts.items():
            amount_currency = currency and company_currency.compute(current_currency, company_currency,
                                                                    values['amount']) \
                              or False
            total_amount += values['nature'] == 'debit' and values['amount'] or - \
                values['amount']
            total_depreciation += values['depreciation']
            total_amount_currency += amount_currency
            amount = values['amount'] and values['amount'] or values['depreciation']
            lines.append(self._prepare_move_line(account_id, amount,
                                                 values['nature'], {}, currency, amount_currency))

        nature = nature == 'debit' and 'credit' or 'debit'
        total_amount = self.asset_move_category_code in ('01', '07') and abs(
            total_amount - total_depreciation) or total_amount
        lines.append(self._prepare_move_line(self.account_id.id, abs(total_amount), nature, {}, currency,
                                             total_amount_currency and total_amount_currency or False))

        account_move.update({
            'line_ids': [(0, 0, line) for line in lines]
        })

        account_move_id = self.env['account.move'].create(account_move)
        account_move_id.post()

        self._confirm_asset_account_move(account_move_id)

    @api.model
    def _confirm_asset_account_move(self, account_move):
        hist = self.env['account.asset.history']
        asset_obj = self.env['account.asset.asset']
        asset_move_history_obj = self.env['l10n_cu.asset.move.history']

        if self.asset_move_category_code in ('01', '02', '07'):
            for asset in self.asset_ids:
                # if not asset.inventory_number:
                #     # inventory = self.env['ir.sequence'].next_by_id(
                #     #     asset.category_id.sequence_id.id)
                #     inventory = asset.category_id.sequence_id.next_by_id()
                # else:
                inventory = asset.inventory_number
                asset.write({
                    'state': 'open',
                    'previous_state': 'open',
                    'area': self.reception_area.id,
                    'inventory_number': inventory,
                    'initial_value': asset.value,
                    'subscribe_date': account_move.date,
                    'sub_ledger_number': self.env['ir.sequence'].get('sub.ledger.seq'),
                })
                history_id = asset_move_history_obj.search(
                    [('asset_move_id', '=', self.id)]).write(
                    {'subscribe_date': account_move.date})
                if asset.parent_id:
                    asset.module_value('add')
                hist_vals = {
                    'name': 'Movements of assets',
                    'date': self.operation_date,
                    'user_id': self.env.user.id,
                    'modification_type': 7,
                    'asset_id': asset.id,
                    'value': asset.value,
                    'move_number': self.number,
                    'value_amount_depreciation': asset.value_amount_depreciation,
                    'active': False,
                }
                hist.create(hist_vals)
                asset.compute_depreciation_board()
            self.reception_area.write({})
        if self.asset_move_category_code in ('03', '05', '06', '12'):
            for asset in self.asset_ids:
                asset.write({'state': 'close',
                             'previous_state': 'close',
                             'area': False,
                             'final_value': asset.value,
                             'unsubscribe_date': account_move.date})
                history_id = asset_move_history_obj.search(
                    [('asset_move_id', '=', self.id)]).write({'unsubscribe_date': account_move.date})
                asset.delete_depreciation_board()
                if asset.parent_id:
                    asset.module_value('rest')

                hist_vals = {
                    'name': 'Movements of assets',
                    'date': self.operation_date,
                    'user_id': self.env.user.id,
                    'modification_type': 7,
                    'value': asset.value,
                    'asset_id': asset.id,
                    'move_number': self.number,
                    'value_amount_depreciation': asset.value_amount_depreciation,
                    'active': False,
                }
                hist.create(hist_vals)
            self.area_id.write({})
        return self.write({'state': 'terminated',
                           'operation_date': account_move.date,
                           'account_move_id': account_move.id,
                           'entered_by': self.env.user.id})

    # def _cancel_asset_account_move(self, cr, uid, asset_move, account_move, context=None):
    #     if asset_move.asset_move_category_code in ('01', '02', '07'):
    #         for asset in asset_move.asset_ids:
    #             if not asset.inventory_number:
    #                 inventory = self.env['ir.sequence'].next_by_id(cr, uid, asset.category_id.sequence_id.id)
    #             else:
    #                 inventory = asset.inventory_number
    #             asset.write({
    #                 'state': 'draft',
    #                 'area': False,
    #                 'inventory_number': False,
    #                 'initial_value': False,
    #                 'subscribe_date': False
    #             })
    #     if asset_move.asset_move_category_code in ('03', '05', '06', '12'):
    #         depreciation_lin_obj = self.env['account.asset.depreciation.line']
    #         depreciation_line_ids_del = depreciation_lin_obj. \
    #             search(cr, uid, [('depreciation_date', '>', account_move.period_id.date_start),
    #                              ('asset_id', '=', asset.id)])
    #         if depreciation_line_ids_del:
    #             depreciation_lin_obj.unlink(cr, uid, depreciation_line_ids_del)
    #         asset.write({'state': 'close',
    #                      'final_value': asset.purchase_value,
    #                      'unsubscribe_date': account_move.date})
    #
    #     employee_id = self.env['hr.employee'].search([('user_id', '=', uid)])[0]
    #     return asset_move.write({'state': 'terminated',
    #                        'operation_date': account_move.date,
    #                        'entered_by': self.env['hr.employee'].browse(employee_id).id})

    @api.multi
    def get_last_move(self):
        return self.search([('state', 'in', ('confirmed', 'terminated')), ('id', 'not in', self.ids)],
                           order='id desc', limit=1)

    @api.multi
    def _prepare_account_move(self):
        account_move = {}
        last_move = self.get_last_move()
        account_move.update({
            # 'module': 'l10n_cu_account_asset',
            'journal_id': self.company_id.asset_journal_id.id,
            'asset_move_id': self.id,
            'ref': self.number
        })
        # if last_move:
        #     account_move.update({
        #         'date': last_move.operation_date,
        #     })
        # else:
        account_move.update({
                'date': self.operation_date,
        })

        if self.asset_move_category_code == '01':
            account_move.update({
                'narration': _('Counting movement of high ') + self.number,
            })
        if self.asset_move_category_code == '02':
            account_move.update({
                'narration': _('Counting movement of purchase ') + self.number,
            })
        if self.asset_move_category_code == '03':
            account_move.update({
                'narration': _('Counting movement of sale ') + self.number,
            })
        if self.asset_move_category_code == '05':
            account_move.update({
                'narration': _('Counting movement of missing adjustment') + self.number,
            })
        if self.asset_move_category_code == '06':
            account_move.update({
                'narration': _('Counting movement of loss adjustment') + self.number,
            })
        if self.asset_move_category_code == '07':
            account_move.update({
                'narration': _('Counting movement of surplus adjustment') + self.number,
            })
        if self.asset_move_category_code == '12':
            account_move.update({
                'narration': _('Counting movement of low') + self.number,
            })
        return account_move

    # @api.multi
    # def _prepare_account_move(self, defaults={}):
    #     last_move = self.get_last_move()
    #     if last_move:
    #         defaults['date'] = last_move.operation_date
    #     defaults['module'] = 'l10n_cu_account_asset'
    #     # account_period = self.env['account.period.module']
    #     defaults['journal_id'] = self.company_id.asset_journal_id.id
    #     defaults['asset_move_id'] = self.id
    #     defaults['ref'] = self.number
    # defaults['period_id'] = account_period._get_active_period('l10n_cu_asset', self.company_id.id).period_id.id

    # if self.env.context.get('to_state') == 'terminated':
    #     self._prepare_asset_account_move(defaults)

    @api.model
    def _prepare_move_line(self, account_id, amount, nature, analyticals, currency, amount_currency):
        return {
            'account_id': account_id,
            'debit': nature == 'debit' and amount or 0.00,
            'credit': nature == 'credit' and amount or 0.00,
            # 'operation_amount': amount,
            # 'nature': nature,
            'currency_id': currency,
            'amount_currency': amount_currency,
            'analytical_restriction': len(analyticals) and True or False,
            'analytic_lines': len(analyticals) and [(0, 0,
                                                     self._prepare_analytical_lines(key, value, currency,
                                                                                    amount_currency))
                                                    for key, value in analyticals.items()] or False
        }

    @api.model
    def _prepare_analytical_lines(self, key, value, currency, amount_currency):
        account_analytic_id = False
        if isinstance(key, int):
            account_analytic_id = key
        else:
            account_analytic_id = key[0]
        return {
            'account_id': account_analytic_id,
            'general_account_id': value['general_account_id'],
            'operation_amount': value['amount'],
            'amount': value['amount'],
            'currency': currency,
            'amount_currency': amount_currency,
            'date': value['date'],
        }

    @api.model
    def _prepare_asset_account_move(self, defaults):
        if self.asset_move_category_code == '01':
            defaults['narration'] = _(
                'Counting movement of high ') + self.number
        if self.asset_move_category_code == '02':
            defaults['narration'] = _(
                'Counting movement of purchase ') + self.number
        if self.asset_move_category_code == '03':
            defaults['narration'] = _(
                'Counting movement of sale ') + self.number
        if self.asset_move_category_code == '05':
            defaults['narration'] = _(
                'Counting movement of missing adjustment ') + self.number
        if self.asset_move_category_code == '06':
            defaults['narration'] = _(
                'Counting movement of loss adjustment ') + self.number
        if self.asset_move_category_code == '07':
            defaults['narration'] = _(
                'Counting movement of surplus adjustment ') + self.number
        if self.asset_move_category_code == '12':
            defaults['narration'] = _(
                'Counting movement of low ') + self.number

        lines = []
        nature = self.asset_move_category_code in (
            '01', '02', '07') and 'debit' or 'credit'
        accounts = self._get_account_values(self, nature)
        company_currency = self.company_id.currency_id.id
        current_currency = self.company_id.asset_journal_id.currency.id
        currency = company_currency != current_currency and current_currency or False
        context = dict(self.env.context)
        context.update({'date': self.operation_date})

        total_amount = 0.00
        total_depreciation = 0.00
        total_amount_currency = 0.00
        for account_id, values in accounts.items():
            amount_currency = currency and company_currency.compute(current_currency, company_currency,
                                                                    values['amount']) \
                              or False
            total_amount += values['nature'] == 'debit' and values['amount'] or - \
                values['amount']
            total_depreciation += values['depreciation']
            total_amount_currency += amount_currency
            amount = values['amount'] and values['amount'] or values['depreciation']
            lines.append(self._prepare_move_line(account_id, amount,
                                                 values['nature'], {}, currency, amount_currency))

        nature = nature == 'debit' and 'credit' or 'debit'
        total_amount = self.asset_move_category_code in ('01', '07') and abs(
            total_amount - total_depreciation) or total_amount
        lines.append(self._prepare_move_line(self.account_id.id, abs(total_amount), nature, {}, currency,
                                             total_amount_currency and total_amount_currency or False))
        defaults['line_id'] = [(0, 0, line) for line in lines]

    @api.model
    def _get_account_values(self, asset_move, nature):
        accounts = {}
        for asset in asset_move.asset_ids:
            account = accounts.setdefault(asset.category_id.account_asset_id.id, {'amount': 0.00, 'nature': nature,
                                                                                  'depreciation': 0.00})
            # account['amount'] += asset.purchase_value
            account['amount'] += asset.value
            if asset_move.asset_move_category_code in ('01', '07') and asset.value_amount_depreciation:
                account = accounts.setdefault(asset.category_id.account_depreciation_id.id, {'amount': 0.00,
                                                                                             'nature': 'credit',
                                                                                             'depreciation': 0.00})
                account['depreciation'] += asset.value_amount_depreciation
            if asset_move.asset_move_category_code not in (
                    # '01', '02', '07') and asset.purchase_value != asset.value_residual:
                    '01', '02', '07') and asset.value != asset.value_residual:
                account = accounts.setdefault(asset.category_id.account_depreciation_id.id, {'amount': 0.00,
                                                                                             'nature': 'debit',
                                                                                             'depreciation': 0.00})
                # account['amount'] += asset.purchase_value - \
                account['amount'] += asset.value - asset.value_residual
        return accounts

    @api.multi
    def reserve_procurement(self):
        context = dict(self.env.context)
        select_product_existence_wizard = self.pool['select.product.existence']
        existence = self.pool['l10n_cu_stock.product_stock_existence']

        availability_ids = existence.search([('availability', '>', 0),
                                             ('company_id', '=',
                                              context['default_company_id']),
                                             ('warehouse_id', '=',
                                              context['warehouse_id']),
                                             ('product_id', '=', context['product_id'])])
        reserve_procurement_wizard = self.env['reserve.procurement.wizard'].create({
        })
        select_product_existence_ids = []
        for id_av in availability_ids:
            select_product_existence_ids.append(select_product_existence_wizard.create({
                'reserve_procurement_id': reserve_procurement_wizard.id,
                'existence_id': id_av,
                'qty_to_reserve': 0.00}).id
                                                )
        if select_product_existence_ids:
            return {
                'name': _('Reserve Procurement Wizard'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'reserve.procurement.wizard',
                'res_id': reserve_procurement_wizard.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                # 'domain': [('id','=',wizard2_ids)],
                'context': {'wizard2_ids': select_product_existence_ids}
            }
        else:
            raise exceptions.except_orm("Error", _(
                "There are no associated existences selected."))

    @api.multi
    def operation_no_account(self, category):
        self.ensure_one()
        company = self.env.user.company_id
        # current_period = self.env['account.period.module']._get_active_period('l10n_cu_asset', company_id)
        # date_start = current_period.period_id.date_start
        date_stop = company.asset_lock_date
        # if self.operation_date < date_start or self.operation_date > date_stop:
        if self.operation_date <= date_stop:
            raise exceptions.except_orm(_('Error !'),
                                        _('The operation date (%s) must be later than %s')
                                        % (self.operation_date, date_stop))
        last_move = self.search([('state', 'in', ('confirmed', 'terminated')), ('id', '!=', self.id)],
                                limit=1, order='operation_date desc')
        if last_move:
            # last_move = move_ids[-1]

            if last_move.operation_date > self.operation_date:
                raise exceptions.except_orm(_('Error !!!'),
                                            _(
                                                'The operation date (%s) can not be lower than the operation date (%s) of the '
                                                'last move made.') % (self.operation_date, last_move.operation_date))
        if self.operation_date < self.approval_date:
            raise exceptions.except_orm(_('Error !!!'),
                                        _('The operation date (%s) can not be lower than the approval date (%s).')
                                        % (self.operation_date, self.approval_date))
        for asset in self.asset_ids:
            if category == '04':
                asset.write({'area': self.reception_area.id})
                asset.area.write(
                    {'number': self.env['ir.sequence'].get('number.seq')})
            elif category == '08':
                asset.set_to_idler()
            elif category == '09':
                asset.write({'state': 'open', 'previous_state': 'open'})
            elif category == '10':
                data = {'rented_asset': True}
                if self.partner_id:
                    data.update({'partner_id': self.partner_id.id})
                asset.write(data)
            elif category == '11':
                data = {'asset_repair': True}
                if self.partner_id:
                    data.update({'partner_id': self.partner_id.id})
                asset.write(data)
        return self.write({
            'state': 'terminated',
            'entered_by': self.env.user.id
        })


class AssetMoveHistory(models.Model):
    _name = 'l10n_cu.asset.move.history'

    name = fields.Char('Name')
    inventory_number = fields.Char('Number of inventory')
    value_amount_depreciation = fields.Float('Amount Depreciation')
    purchase_value = fields.Float('Gross Value')
    subscribe_date = fields.Date('Date of subscribe')
    unsubscribe_date = fields.Date('Date of unsubscribe')
    asset_move_id = fields.Many2one('l10n_cu.asset.move', 'Asset move')


class AccountAssetDepreciationLine(models.Model):
    """
    Class purpose:
        - To save all data related to the depreciation of assets

    Type of inheritances used:
        - Class Inheritance.

    Inheritance Purpose:
        - Used to extend the functionalities of the asset depreciation.

    Inherited model:
        - account.asset.depreciation.line

    Model Fields:

        - company_id: { type: (many2one), help: (Company) }
        - company_code: { type: (char), help: (Company code) }
        - inventory_number: { type: (char), help: (Number inventory) }
        - purchase_value: { type: (float), help: (Acquisition value) }
        - discharge_date: { type: (date), help: (Discharge date) }
        - close_date: { type: (date), help: (Close date) }
        - depreciation_tax: { type: (float), help: (Depreciation tax) }
        - remaining_value: { type: (float), help: (Amount to Depreciate) }
        - state: { type: (selection), help: (State), values: (Draft, Ready, Posted) }
        - move_check: { type: (function), help: (Moves posted) }
        - amount: { type: (float), help: (Depreciation Amount) }
        - wizard_id: { type: (many2one), help: (Depreciation with error) }
        - category_id: { type: (many2one), help: (Asset category) }
        - depreciated_value: { type: (float), help: (Amount Already Depreciated) }
        - emission_number: { type: (char), help: (Number of model) }
        - asset_module_id: { type: (many2one), help: (Asset module) }
        - asset_id: { type: (many2one), help: (Asset) }
        - is_check: { type: (boolean), help: (Is check the depreciation asset) }

    Related Views:
        - view_depreciation_line_search_tree: {type : (tree) }
        - view_depreciation_line_search: {type : (search) }
    """
    _name = 'account.asset.depreciation.line'
    _description = 'Asset depreciation line'
    _inherit = 'account.asset.depreciation.line'
    _order = 'depreciation_date'
    # required name, sequence, asset_id, amount, remaining_value, depreciated_value,

    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    company_code = fields.Char('Company code', size=16, readonly=True)

    inventory_number = fields.Char('Number inventory', size=16, readonly=True)
    purchase_value = fields.Float(
        'Acquisition value', readonly=True, digits=dp.get_precision('Account'))
    discharge_date = fields.Date(
        'Discharge date', help="Discharge date", readonly=True)
    close_date = fields.Date('Close date', help="Close date", readonly=True)
    depreciation_tax = fields.Float(
        'Depreciation tax', digits=dp.get_precision('Account'))
    state = fields.Selection([('draft', 'Draft'), ('ready', 'Ready'), ('posted', 'Posted')], 'State', required=True,
                             default='draft')
    wizard_id = fields.Many2one(
        'l10n_cu.asset.depreciation.error', 'Wizard', required=False)
    category_id = fields.Many2one('account.asset.category', 'Asset category')
    emission_number = fields.Char("Number of model", size=255, default=lambda s: s.env['ir.sequence']
                                  .get('move_depreciation_asset_sequence'),
                                  states={'confirmed': [('readonly', True)], 'canceled': [('readonly', True)]})
    is_check = fields.Boolean('Is check the depreciation asset', default=True)
    asset_or_module = fields.Char("Module Asset and Asset", size=255)

    @api.multi
    def check_backs_depreciation(self):
        self.ensure_one()
        depreciation_line = self.search([('sequence', '<', self.sequence),
                                         ('asset_id', '=', self.asset_id.id)], limit=1,
                                        order="sequence desc")
        return depreciation_line.move_id and False or True

    @api.multi
    def check_depreciation_now(self):
        self.ensure_one()
        period_obj = self.env['account.period']
        asset_period_close_obj = self.env['l10n_cu.asset.period.close']
        now_date = time.strftime('%Y-%m-%d')
        period_ids = period_obj.find(now_date)
        period_objs = period_obj.browse(period_ids)
        period_objs = period_objs[0]
        if period_objs.date_start != self.depreciation_date:
            depreciation_period_ids = period_obj.find(self.depreciation_date)
            asset_period_close_id = asset_period_close_obj._get_last_period([])
            if depreciation_period_ids:
                if depreciation_period_ids[0] == asset_period_close_id:
                    return True
                else:
                    return False
            return False
        else:
            return False

    @api.multi
    def period_actual(self):
        now_date = datetime.now()
        for depreciation_line in self:
            if now_date.month < datetime.strptime(depreciation_line.depreciation_date, '%Y-%m-%d').month:
                return False
        return True

    @api.one
    def period_close(self):
        move_ids = self.env['l10n_cu.asset.move'].search(
            [('operation_date', '<=', self.asset_id.company_id.asset_lock_date),
             ('state', 'not in', ('draft', 'confirmed'))])
        if move_ids and self.depreciation_date < self.asset_id.company_id.asset_lock_date and self.state == 'posted':
            return True
        return False

    @api.multi
    def account_journal_validate(self):
        for line in self:
            if line.asset_id:
                if not line.asset_id.company_id.asset_journal_id:
                    raise exceptions.except_orm(_('Warning !'), _(
                        'Do not have journal type configure.'))
                if not line.asset_id.category_id.account_depreciation_id.id:
                    raise exceptions.except_orm(_('Warning !'), _(
                        'Do not have depreciation account configure.'))

                if not line.asset_id.area.account_depreciation_expense_id.id:
                    raise exceptions.except_orm(_('Warning !'),
                                                _('Do not have the depreciation expense account configure.'))

    @api.multi
    def before_period_posted(self):
        for depreciation_line in self:
            lines_ids = []
            if depreciation_line.asset_id:
                lines_ids.append(self.search(
                    [('asset_id', '=', depreciation_line.asset_id.id)]))
            var = False
            for line in lines_ids:
                if line.id == depreciation_line.id:
                    var = True
                elif not var and line.state != 'posted':
                    return True
        return False

    @api.multi
    def validate_create_move_rules(self):
        if self.before_period_posted():
            raise exceptions.except_orm(_('Warning !'), _('You can not create move of depreciation because there '
                                                          'previous months without depreciate.'))
        self.account_journal_validate()
        return True

    @api.model
    def compute_year_depreciation_tax(self, asset_id, depreciation_date):
        ym = 0
        current_year = depreciation_date.strftime('%Y')
        depreciation_line_ids = self.search([('asset_id', '=', asset_id)])
        if depreciation_line_ids:
            depreciation_objs = self.browse(depreciation_line_ids)
            ym = [s.amount for s in depreciation_objs if
                  datetime.strptime(s.depreciation_date, '%Y-%m-%d').year == int(current_year)]
        a = sum(ym)
        return a

    @api.multi
    def create_move(self, line_ids, defaults={}, post_move=True):
        ald = False
        created_moves = self.env['account.move']
        prec = self.env['decimal.precision'].precision_get('Account')

        for line in line_ids:
            ald = datetime.strptime(line.asset_id.company_id.asset_lock_date, '%Y-%m-%d')
            ldd = datetime.strptime(line.depreciation_date, '%Y-%m-%d')
            if ald > ldd:
                raise exceptions.except_orm(_('Error !'), _('You can not depreciate because the depreciation date (%s) '
                                                            'must be later than %s.') % (
                                                line.depreciation_date,
                                                line.asset_id.company_id.asset_lock_date))

            model_obj = self.env['ir.model.data']
            if not line.asset_id.company_id.asset_journal_id:
                msg = _('You do not have an asset journal configured for your company.\n Please, go to the asset '
                        'configuration and select the asset journal.')
                model, action_id = model_obj.get_object_reference(
                    'l10n_cu_account_asset', 'action_asset_config_settings')
                raise exceptions.RedirectWarning(
                    msg, action_id, _('Go to the asset configuration panel'))

            # preparing account move
            defaults['asset_id'] = line.asset_id
            defaults['journal_id'] = line.asset_id.company_id.asset_journal_id.id
            depreciation_date = self.env.context.get(
                'depreciation_date') or line.depreciation_date or fields.Date.context_today(self)
            sequence = line.asset_id.company_id.asset_journal_id.sequence_id
            new_name = sequence.with_context(ir_sequence_date=depreciation_date).next_by_id()
            move_name = '(%s)' % new_name

            depreciation_date = self.env.context.get(
                'depreciation_date') or line.depreciation_date or fields.Date.context_today(self)
            company_currency = line.asset_id.company_id.currency_id
            current_currency = line.asset_id.currency_id
            amount = current_currency.with_context(date=depreciation_date).compute(line.amount, company_currency)
            asset_name = line.asset_id.name + ' (%s/%s)' % (line.sequence, len(line.asset_id.depreciation_line_ids))
            category_id = line.asset_id.category_id

            move_line_1 = {
                'name': asset_name,
                'account_id': category_id.account_depreciation_id.id,
                'narration': _('Depreciating the asset %s') % line.asset_id.inventory_number,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'journal_id': line.asset_id.company_id.asset_journal_id.id,
                'partner_id': line.asset_id.partner_id.id,
                'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'sale' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - 1.0 * line.amount or 0.0,
            }
            move_line_2 = {
                'name': asset_name,
                'account_id': category_id.account_depreciation_expense_id.id,
                'narration': _('Depreciating the asset %s') % line.asset_id.inventory_number,
                'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'journal_id': line.asset_id.company_id.asset_journal_id.id,
                'partner_id': line.asset_id.partner_id.id,
                'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'purchase' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and line.amount or 0.0,
            }
            # self._prepare_depreciation_account_move(line, defaults)

            account_move = {}

            account_move.update({
                'name': move_name,
                'journal_id': defaults['journal_id'],
                'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
                'date': date.today(),
                'ref': 'Depreciacion_' + format(depreciation_date),
            })

            account_move_id = self.env['account.move'].create(account_move)

            account_move_id.post()
            line.write({'move_id': account_move_id.id, 'move_check': True, 'state': 'posted'})

            self._confirm_account_move(account_move_id)




    @api.multi
    def _prepare_account_move(self, defaults):
        # self.ensure_one()
        # defaults['date'] = depreciation.depreciation_date
        defaults['module'] = 'l10n_cu_account_asset'
        # account_period = self.env['account.period.module']
        defaults['journal_id'] = defaults['asset_id'].company_id.asset_journal_id.id
        # defaults['ref'] = depreciation.emission_number
        # defaults['period_id'] = account_period._get_active_period('l10n_cu_asset', self.asset_id.company_id.id).period_id.id
        self._prepare_depreciation_account_move(defaults)

    @api.model
    def _prepare_depreciation_account_move(self, line_ids, defaults):
        if len(defaults['asset_id']) == 1:
            defaults['narration'] = _(
                'Depreciating the asset %s') % defaults['asset_id'].inventory_number
        else:
            defaults['narration'] = _('Depreciating assets')

        lines = []
        accounts = self._get_depreciation_values(line_ids)
        company_currency = defaults['asset_id'].company_id.currency_id.id
        current_currency = defaults['asset_id'].company_id.asset_journal_id.currency_id.id
        currency = company_currency != current_currency and current_currency or False

        total_amount = 0.00
        total_amount_currency = 0.00
        for account_id, values in accounts.items():
            amount_currency = currency and company_currency.compute(current_currency, company_currency,
                                                                    values['amount']) or False
            total_amount += values['nature'] == 'debit' and values['amount'] or - \
                values['amount']
            total_amount_currency += amount_currency
            lines.append(
                self.env['l10n_cu.asset.move']._prepare_move_line(account_id, values['amount'], values['nature'],
                                                                  values['analyticals'], currency, amount_currency))

        defaults['line_id'] = [(0, 0, line) for line in lines]

    @api.model
    def _get_depreciation_values(self, line_ids):
        accounts = {}
        for depreciation in line_ids:
            account_expense_id = depreciation.asset_id.area.account_depreciation_expense_id
            account_analytical_id = depreciation.asset_id.area.account_analytic_id
            account = accounts.setdefault(depreciation.asset_id.category_id.account_depreciation_id.id,
                                          {'amount': 0.00,
                                           'nature': 'credit',
                                           'analyticals': {}})
            account['amount'] += depreciation.amount
            account = accounts.setdefault(account_expense_id.id,
                                          {'amount': 0.00,
                                           'nature': 'debit',
                                           'analyticals': {}})
            account['amount'] += depreciation.amount
            if account_analytical_id:
                analytical = account['analyticals'].setdefault(account_analytical_id.id,
                                                               {'amount': 0.00,
                                                                'general_account_id': account_expense_id.id,
                                                                'date': depreciation.depreciation_date})
                analytical['amount'] += depreciation.amount
        return accounts

    @api.multi
    def _confirm_account_move(self, account_move):
        for depreciation in account_move:
            depreciation.write({'move_id': account_move.id,
                                'state': 'posted'})
        self._confirm_asset_depreciation(account_move)

    @api.model
    def _confirm_asset_depreciation(self, account_move):
        if account_move:
            depreciation_ids = self.search([('move_id', '=', account_move.id)])
            for depreciation in depreciation_ids:
                asset = depreciation.asset_id
                asset.write(
                    {'value_amount_depreciation': asset.value_amount_depreciation + depreciation.amount})
                asset.compute_depreciation_board()
                history_vals = {
                    'asset_id': asset.id,
                    'company_id': asset.company_id.id,
                    'name': _('Depreciating the asset - %s') % asset.name,
                    'method': asset.method,
                    'method_period': asset.method_period,
                    'user_id': self.env.user.id,
                    'date': depreciation.depreciation_date,
                    'inventory_number': asset.inventory_number,
                    'modification_type': 6,
                    'depreciation_value': depreciation.amount,
                    'purchase_value': depreciation.purchase_value,
                    'value_amount_depreciation': asset.value_amount_depreciation
                }
                self.env['account.asset.history'].create(history_vals)

    @api.multi
    def _check_moves(self, method):
        for depreciation_line in self:
            if depreciation_line.move_id:
                if method == 'write':
                    raise exceptions.except_orm(_('Error !'), _('You can not desactivate a depreciation line that '
                                                                'contains some journal items.'))
                elif method == 'unlink':
                    raise exceptions.except_orm(_('Error !'),
                                                _('You can not remove a depreciation line with journal items.'))
        return True

    @api.multi
    def unlink(self):
        self._check_moves("unlink")
        return super(AccountAssetDepreciationLine, self).unlink()

    @api.multi
    def set_to_posted(self):
        return self.write({'state': 'posted'})

    @api.multi
    def move_ready(self):
        return self.create_move()

    @api.multi
    def move_posted(self):
        self.write({'state': 'posted'})
        return True

    @api.multi
    def move_draft(self):
        move_obj = self.env['account.move']
        for asset_depreciation_line in self:
            if not asset_depreciation_line.move_id:
                return self.write({'state': 'draft'})
            asset_depreciation_line_after = self.search(
                [('depreciation_date', '>', asset_depreciation_line.depreciation_date),
                 ('state', 'in', ('ready', 'posted'))])
            if asset_depreciation_line_after:
                raise exceptions.except_orm(_('Warning'),
                                            _(
                                                'You can not reverse the depreciation because no proof made ​​subsequent depreciation.'))
            else:
                if asset_depreciation_line.depreciation_date > asset_depreciation_line.asset_id.company_id.asset_lock_date:
                    raise exceptions.except_orm(_('Warning'),
                                                _('You can not reverse done depreciations.'))
            if asset_depreciation_line.move_id.state == 'draft':
                return move_obj.unlink([asset_depreciation_line.move_id.id])
        return self.create_move()


class l10n_cuMonthPlanning(models.Model):
    _name = "l10n_cu.month.planning"
    _description = "Month"

    name = fields.Char('Month', size=64, required=True, translate=True)
    number = fields.Char('Number Month', size=64, required=True)
    init_year = fields.Boolean('Init Year')
    finish_year = fields.Boolean('Finish Year')


class l10n_cuMonthlyDepreciationEntries(models.Model):
    _name = "l10n_cu.monthly.depreciation.entries"
    _description = "Entries the depreciation monthly"

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = record.asset_id.id
            res.append((record.id, name))
        return res

    asset_id = fields.Many2one('account.asset.asset', 'Asset Depreciation Monthly')
    date_high = fields.Datetime('High date', readonly=True)
    date_low = fields.Datetime('Low date', readonly=True)
    company_id = fields.Many2one(
        'res.company', 'Company', readonly='True', default=lambda s: s.env.user.company_id)


class l10n_cuMonthlyDepreciationEntriesLines(models.Model):
    _name = "l10n_cu.monthly.depreciation.entries.lines"
    _description = "Entries the depreciation monthly"

    month_line = fields.Many2one(
        'l10n_cu.month.planning', 'Planning month depreciation')
    depreciation_entries_id = fields.Many2one(
        'l10n_cu.monthly.depreciation.entries', 'Entries the depreciation')
    depreciation_value = fields.Float('Depreciation value', required=True)
    year = fields.Char('Year', size=64, required=True)
