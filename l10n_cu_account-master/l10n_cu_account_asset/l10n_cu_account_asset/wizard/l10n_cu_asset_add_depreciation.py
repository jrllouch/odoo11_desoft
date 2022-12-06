# -*- coding: utf-8 -*-
import time
from odoo import fields, models, api, exceptions, _


class l10n_cu_AssetAddDepreciation(models.AbstractModel):
    _name = 'l10n_cu.asset.add.depreciation'
    _description = "Add depreciation to the asset in the high movement"

    asset_id = fields.Many2one('account.asset.asset', 'Asset')
    value_amount_depreciation = fields.Float('Amount Depreciation')

    @api.model
    def default_get(self, field):
        context = dict(self.env.context)
        res = super(l10n_cu_AssetAddDepreciation, self).default_get(field)
        if context.get('active_id', False):
            asset = self.pool.get('account.asset.asset').browse(context.get('active_id'))
            res['asset_id'] = asset.id
            res['value_amount_depreciation'] = asset.value_amount_depreciation
        return res

    @api.multi
    def accept(self):
        context = dict(self.env.context)
        data = dict({
            'ids': context.get('active_ids', []),
            'model': context.get('active_model', 'ir.ui.menu'),
            'form': False,
            'extra': False
        })
        data['form'] = self.read(['asset_id', 'value_amount_depreciation'])[0]
        asset_id = data['form']['asset_id'][0]
        new_depreciation = data['form']['value_amount_depreciation']
        asset = self.pool.get('account.asset.asset').browse(asset_id)
        if new_depreciation > asset.value:
            raise exceptions.except_orm(_('Error !'), _("The new depreciation value (%s) can not be greater than the "
                                                        "asset purchase value (%s)!") % (new_depreciation, asset.value))
        asset.write({'value_amount_depreciation': new_depreciation})
