from odoo import fields, osv, api, models, exceptions
from odoo import _


class l10n_cu_AssetAddComponents(models.Model):
    _name = 'l10n_cu.asset.add.components'
    _description = "Add components to the Control module/Functional unit"

    def _get_asset(self):
        context = dict(self.env.context)
        if context.get('active_id', False):
            asset_obj = self.env['account.asset.asset'].browse(context.get('active_id'))
            return asset_obj.id
        return False

    asset_id = fields.Many2one('account.asset.asset', 'Control module/Functional unit')
    asset_ids = fields.Many2many('account.asset.asset', 'add_components_account_asset_rel', 'component_id',
                                 'account_id', 'Assets', default=_get_asset)
    company_id = fields.Many2one('res.company', 'Company', required=False, default=lambda s: s.env.user.company_id)

    @api.multi
    def add_components(self):
        context = dict(self.env.context)
        res = {'value': {}}
        sum_purch = sum_resid = sum_depre = 0.00
        data = dict({
            'ids': context.get('active_ids', []),
            'model': context.get('active_model', 'ir.ui.menu'),
            'form': False
        })
        data['form'] = self.read(['asset_id', 'asset_ids'])[0]

        if data['form']['asset_ids']:
            asset_obj = self.env['account.asset.asset']
            asset_mod = asset_obj.browse(data['form']['asset_id'][0])
            sum_purch = asset_mod.value
            sum_resid = asset_mod.value_residual
            sum_depre = asset_mod.depreciated_value
            for a in data['form']['asset_ids']:
                asset = asset_obj.browse(a)
                inventory = asset_mod.consec(asset_mod.inventory_number)
                asset_obj.write({'parent_id': data['form']['asset_id'][0], 'inventory_number': inventory})
                sum_purch = sum_purch + asset.value
                sum_resid = sum_resid + asset.value_residual
                sum_depre = sum_depre + asset.depreciated_value

            asset_obj.write({'value': sum_purch, 'value_residual': sum_resid, 'depreciated_value': sum_depre,
                             'state': 'open'})
            # asset_obj.compute_depreciation_board(data['form']['asset_id'][0])
        else:
            raise exceptions.except_orm(_('Warning !'), _('You can not leave empty the assets list!'))

        return res
