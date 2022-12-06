# -*- coding: utf-8 -*-
'''
    This file contains the code to print the "Asset transfer" Report
'''
# from chardet.test import result
import time
from odoo import models, fields, api


class l10n_cu_sub_ledger_asset_countable_report(models.AbstractModel):
    _name = 'report.l10n_cu_account_asset.l10n_cu_subldgr_asset_count_report'

    @api.model
    def get_report_values(self, docids, data=None):
        final_list = []
        asset = self.env['account.asset.asset'].browse(data['form']['asset_id'])
        initial_date = data['form']['initial_date']
        final_date = data['form']['final_date']
        move_obj = self.env['l10n_cu.asset.move']
        history_obj = self.env['account.asset.history']
        if initial_date and final_date:
            history_ids = history_obj.search([('date', '>=', initial_date),
                                             ('date', '<=', final_date),
                                             ('asset_id', '=', asset.id),
                                             ('modification_type', 'in', (2, 5, 6, 7, 8)),
                                              '|', ('active', '=', False),
                                              ('active', '=', True)])
        else:
            history_ids = history_obj.search([('asset_id', '=', data['form']['asset_id']),
                                              ('modification_type', 'in', (2, 5, 6, 7, 8)),
                                              '|', ('active', '=', False),
                                              ('active', '=', True)], order='id desc')

        if history_ids:
            # history_ids.reverse()
            prev_depreciation_value = history_ids[0].value_amount_depreciation
            for history in history_ids:
                inc_val = True
                inc_depre = True
                if history.modification_type == 7:  # movimiento
                    move = move_obj.search([('number', '=', history.move_number), ('company_id', '=', asset.company_id.id)])
                    move = move_obj.browse(move.id)
                    concept = move.asset_move_category_code
                    if move.asset_move_category_code not in ('01', '02', '07'):
                        inc_val = False
                elif history.modification_type == 2:  # reevaluacion
                    concept = '13'
                    inc_val = history.value > history.previous_value and True or False
                elif history.modification_type == 5:  # inicial
                    concept = '14'
                elif history.modification_type == 8:  # depreciation value
                    concept = '16'
                    inc_depre = history.value_amount_depreciation > prev_depreciation_value and True or False
                    prev_depreciation_value = history.value_amount_depreciation
                else:   # depreciacion
                    concept = '15'

                values = {
                    'date': history.date,
                    'doc_number': history.move_number and history.move_number or False,
                    'concept': concept,
                    'value': history.value,
                    'depreciation': history.depreciation_value,
                    'total_depreciation': history.value_amount_depreciation,
                    'inc_val': inc_val,
                    'inc_depre': inc_depre,
                }
                final_list.append(values)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'data': data['form'],
            'final_list': final_list,
            'asset': asset,
        }




