# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _


class l10n_cu_AccountMove(models.Model):
    _inherit = 'account.move'

    asset_move_id = fields.Many2one('l10n_cu.asset.move', 'Asset move')
    asset_modification_id = fields.Many2one('l10n_cu.asset.modify.info', 'Asset modification')

    # @api.onchange('date')
    # def onchange_date(self):
    #     if self._context.get('active_model') == 'l10n_cu.asset.move':
    #         move = self.env['l10n_cu.asset.move'].search([('id', '=', self._context.get('active_id'))])
    #         move.write({'operation_date': self.date})

    @api.one
    @api.constrains('date')
    def _check_asset_validation(self):
        if self._context.get('active_model', False) == 'l10n_cu.asset.move':
            move = self.env['l10n_cu.asset.move'].browse(self._context.get('active_id'))
            move_ids = self.env['l10n_cu.asset.move'].search([('state', 'in', ('confirmed', 'terminated')),
                                                         ('id', '!=', move.id)])
            if move_ids:
                last_move = move_ids[-1]
                if last_move.operation_date > self.date:
                    raise exceptions.ValidationError(_('The operation date (%s) can not be lower than the operation date (%s) of the last move made.')%(self.date, last_move.operation_date))

            if self.date < move.approval_date:
                raise exceptions.ValidationError(_('The operation date (%s) can not be lower than the approval date (%s).')%(self.date, move.approval_date))

            for asset in move.asset_ids:
                if self.date < asset.purchase_date:
                    raise exceptions.ValidationError(_('The operation date (%s) can not be lower than the asset purchase date (%s - %s)')%(self.date, asset.name, asset.purchase_date))



