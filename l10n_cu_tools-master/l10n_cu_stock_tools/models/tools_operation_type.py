# -*- coding: utf-8 -*-

from odoo import models, fields, api
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ToolsPickingType(models.Model):
    _inherit = 'tools.picking.type'

    code = fields.Selection(selection_add=[('stock_operation', 'Stock Outgoing Operation')])
    # Statistics for the kanban view

    count_picking_ready = fields.Integer(compute='_compute_stock_picking_count')
    count_picking_draft = fields.Integer(compute='_compute_stock_picking_count')
    count_picking_waiting = fields.Integer(compute='_compute_stock_picking_count')
    count_picking_late = fields.Integer(compute='_compute_stock_picking_count')
    count_picking_backorders = fields.Integer(compute='_compute_stock_picking_count')

    count_picking = fields.Integer(compute='_compute_stock_picking_count')
    rate_picking_late = fields.Integer(compute='_compute_stock_picking_count')
    rate_picking_backorders = fields.Integer(compute='_compute_stock_picking_count')

    def _get_action(self, action_xmlid):
        # TDE TODO check to have one view + custo in methods
        action = self.env.ref(action_xmlid).read()[0]
        if self:
            action['domain'] = "[('custodian_dest_id', '!=', False), ('company_id', '=', " + str(self.company_id.id) + ")]"
        return action

    def get_stock_picking_action_picking_type(self):
        return self._get_action('l10n_cu_stock_tools.stock_tools_picking_action_picking_type')

    def get_stock_action_picking_tree_waiting(self):
        return self._get_action('l10n_cu_stock_tools.action_stock_picking_tree_waiting')

    def get_action_stock_picking_tree_ready(self):
        return self._get_action('l10n_cu_stock_tools.action_stock_picking_tree_ready')

    def get_action_stock_picking_tree_waiting(self):
        return self._get_action('stock.action_picking_tree_waiting')

    def get_action_stock_picking_tree_late(self):
        return self._get_action('stock.action_picking_tree_late')

    def get_action_stock_picking_tree_backorder(self):
        return self._get_action('stock.action_picking_tree_backorder')

    def _compute_stock_picking_count(self):
        # TDE TODO count picking can be done using previous two
        domains = {
            'count_picking_draft': [('state', '=', 'draft')],
            'count_picking_waiting': [('state', 'in', ('confirmed', 'waiting'))],
            'count_picking_ready': [('state', '=', 'assigned')],
            'count_picking': [('state', 'in', ('assigned', 'waiting', 'confirmed'))],
            'count_picking_late': [('scheduled_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)), ('state', 'in', ('assigned', 'waiting', 'confirmed'))],
            'count_picking_backorders': [('backorder_id', '!=', False), ('state', 'in', ('confirmed', 'assigned', 'waiting'))],
        }
        for field in domains:
            data = self.env['stock.picking'].read_group(domains[field] +
                [('state', 'not in', ('done', 'cancel')), ('custodian_dest_id', '!=', False), ('company_id', '=', self[0].company_id.id)],
                ['picking_type_id'], ['picking_type_id'])
            count = {
                x['picking_type_id'][0]: x['picking_type_id_count']
                for x in data if x['picking_type_id']
            }
            for record in self:
                result=0
                for cuenta in count:
                    result += count.get(cuenta, 0)
                record[field] = result
        for record in self:
            record.rate_picking_late = record.count_picking and record.count_picking_late * 100 / record.count_picking or 0
            record.rate_picking_backorders = record.count_picking and record.count_picking_backorders * 100 / record.count_picking or 0
