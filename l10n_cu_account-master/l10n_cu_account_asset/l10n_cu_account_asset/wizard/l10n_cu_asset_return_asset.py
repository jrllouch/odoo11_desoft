from odoo import fields, api, exceptions, models
from odoo import _


class l10n_cu_AssetReturnAsset(models.Model):
    _name = 'l10n_cu.asset.return.asset'
    _description = "Return a rented/repaired asset"

    def _get_asset(self):
        context = dict(self.env.context)
        if context.get('active_id', False):
            asset_obj = self.env['account.asset.asset'].browse(context.get('active_id'))
            return asset_obj.id
        return False

    def _get_asset_movement(self):
        context = dict(self.env.context)
        if context.get('active_id', False):
            move_obj = self.env['l10n_cu.asset.move']
            move_categ_obj = self.env['l10n_cu.asset.move.category']
            move_categ_ids = move_categ_obj.search([('code', 'in', ('10', '11'))])
            if context.get('asset_repair'):
                asset_move_category_id = move_categ_ids[1]
            elif context.get('rented_asset'):
                asset_move_category_id = move_categ_ids[0]
            move_ids = move_obj.search([('asset_ids', 'in', context.get('active_id')), ('state', '=', 'terminated'),
                                        ('asset_move_category_id', '=', asset_move_category_id.id),
                                        ('return_date', '=', False)])
            return move_ids.id
        return False

    asset_id = fields.Many2one('account.asset.asset', 'Asset', default=_get_asset)
    movement_id = fields.Many2one('l10n_cu.asset.move', 'Movement document', default=_get_asset_movement)
    company_id = fields.Many2one('res.company', 'Company', required=False, default=lambda s: s.env.user.company_id)
    return_date = fields.Date('Return date', required=True)

    @api.multi
    def return_asset(self):
        context = dict(self.env.context)
        res = {'value': {}}

        data = dict({
            'ids': context.get('active_ids', []),
            'model': context.get('active_model', 'ir.ui.menu'),
            'form': False
        })

        data['form'] = self.read(['asset_id', 'return_date', 'movement_id'])[0]
        mov_obj = self.env['l10n_cu.asset.move']
        if data['form'].get('movement_id', False):
            mov_mod = mov_obj.browse(data['form']['movement_id'][0])

            if data['form']['return_date'] >= mov_mod.operation_date:
                if context.get('asset_repair'):
                    self.asset_id.write({'asset_repair': False, 'partner_id': False})
                elif context.get('rented_asset'):
                    self.asset_id.write({'rented_asset': False, 'partner_id': False})
                mov_obj.write({'return_date': data['form']['return_date']})
            else:
                raise exceptions.except_orm(_('Warning !'), _(
                    "The return date (%s) can't be less than the operation date of the movement (%s)!") % (
                                     data['form']['return_date'], mov_mod.operation_date))
        else:
            if context.get('asset_repair'):
                self.asset_id.write({'asset_repair': False, 'partner_id': False})
            elif context.get('rented_asset'):
                self.asset_id.write({'rented_asset': False, 'partner_id': False})
        return res
