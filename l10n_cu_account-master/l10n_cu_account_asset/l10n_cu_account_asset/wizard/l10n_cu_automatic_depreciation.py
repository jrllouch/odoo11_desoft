# -*- coding: utf-8 -*-
from odoo import fields, api, models, exceptions, _
from datetime import datetime, date
import calendar


class l10n_cu_AutomaticDepreciationAsset(models.TransientModel):
    _name = 'l10n_cu.automatic.depreciation.asset'
    _description = 'Automatic Asset Depreciation'

    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda s: s.env.user.company_id.id)
    depreciate_until_date = fields.Date('Depreciate until', help='Limits the date for assets to be depreciated',
                                        default=date.today(), required=True)

    @api.multi
    def next(self):
        depreciation_obj = self.env['account.asset.depreciation.line']
        company_id = self.env.user.company_id
        depreciation_ids = depreciation_obj.search(
            [('state', '=', 'draft'), ('asset_id.company_id', '=', company_id.id),
             ('depreciation_date', '<=', self.depreciate_until_date)])
        if not depreciation_ids:
            raise exceptions.except_orm(_('Error !'),
                                        _('There are no more assets to depreciate until the date provided.'))

        depreciation_obj.create_move(depreciation_ids, post_move=True)

        depreciation_ids_post = depreciation_obj.search(
            [('state', '=', 'draft'), ('asset_id.company_id', '=', company_id.id),
             ('depreciation_date', '<=', self.depreciate_until_date)])

        if depreciation_ids_post:
            return self.next()
        else:
            message_id = self.env['l10n_cu.asset.success'].create({'message': _('Have been depreciated %s assets in '
                                                                                'the date provided.') % (
                                                                                  len(depreciation_ids))})
            return {
                'name': _('Success operation'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'l10n_cu.asset.success',
                'res_id': message_id.id,
                'target': 'new'
            }

    @api.multi
    @api.onchange('depreciate_until_date')
    def onchange_depreciate_until_date(self):
        if self.depreciate_until_date:
            company_id = self.env.user.company_id
            depreciation_obj = self.env['account.asset.depreciation.line']
            depreciation_ids = depreciation_obj.search(
                [('state', '=', 'draft'), ('asset_id.company_id', '=', company_id.id),
                 ('depreciation_date', '<=', self.depreciate_until_date), ])
            pass

    @api.multi
    def _prepare_account_move(self, defaults):
        depreciation_obj = self.env['account.asset.depreciation.line']
        return depreciation_obj._prepare_account_move(defaults)


class l10n_cu_AssetDepreciationError(models.Model):
    _name = 'l10n_cu.asset.depreciation.error'
    _description = 'The Depreciation line with error'
    _rec_name = 'id'

    @api.model
    def _get_lines_depreciation(self):
        ids = []
        context = dict(self.env.context)
        if context.get('depreciation_line_error_ids', False):
            ctx_key = 'depreciation_line_error_ids' if context.get('depreciation_line_error_ids', False) else []
            for line in context.get(ctx_key, []):
                ids.append(line)
        return ids

    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda s: s.env.user.company_id.id)
    depreciation_line_ids = fields.One2many('account.asset.depreciation.line', 'wizard_id', 'The Depreciation Lines',
                                            readonly=True)
    state = fields.Selection([('one', 'One'), ('two', 'Two'), ('three', 'Three')], 'State')

    @api.model
    def default_get(self, fields):
        res = super(l10n_cu_AssetDepreciationError, self).default_get(fields)
        context = dict(self.env.context)
        if context.get('depreciation_line_error_ids', False):
            depreciation_ids = context.get('depreciation_line_error_ids', [])
            res['depreciation_line_ids'] = depreciation_ids
            res['state'] = 'one'
        elif context.get('message', False):
            if context['message'] == 1:
                res['state'] = 'two'
            elif context['message'] == 2:
                res['state'] = 'three'
        return res

    @api.multi
    def go_account_asset_asset(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        result = mod_obj.get_object_reference(
            'account_asset', 'action_account_asset_asset_form')
        ident = result and result[1] or False
        result = act_obj.read([ident])[0]
        return result
