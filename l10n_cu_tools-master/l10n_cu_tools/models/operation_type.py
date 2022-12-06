# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class OperationType(models.Model):
    _name = 'tools.picking.type'

    name = fields.Char('Operation Types Name', required=True, translate=True)
    color = fields.Integer('Color')
    sequence = fields.Integer('Sequence', help="Used to order the 'All Operations' kanban view")
    sequence_id = fields.Many2one('ir.sequence', 'Reference Sequence', required=True)
    code = fields.Selection([
        ('income', 'Entrance'),
        ('income_surplus', 'Entry for Surplus'),
        ('outgoing', 'Out'),
        ('outgoing_Missing', 'Out for Missing'),
        ('internal', 'Internal Transfer'),
        ('income_transfer', 'Income Dependencies Transfer'),
        ('outgoing_transfer', 'Outgoing Dependencies Transfer'),
    ], required=True)
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env['res.company']._company_default_get('l10n_cu_tools_storage.operation_type'),
        index=1)
    active = fields.Boolean('Active', default=True)
    count_tpicking_draft = fields.Integer(compute='_compute_picking_count')
    count_tpicking_confirmed = fields.Integer(compute='_compute_picking_count')
    count_tpicking_done = fields.Integer(compute='_compute_picking_count')
    count_tpicking_cancel = fields.Integer(compute='_compute_picking_count')

    def _compute_picking_count(self):
        # TDE TODO count picking can be done using previous two
        domains = {
            'count_tpicking_draft': [('state', '=', 'draft')],
            'count_tpicking_confirmed': [('state', '=', 'confirmed')],
            'count_tpicking_done': [('state', '=', 'done')],
            'count_tpicking_cancel': [('state', '=', 'cancel')],
        }
        for field in domains:
            data = self.env['tools.picking'].read_group(domains[field] +
                [('picking_type_id', 'in', self.ids)],
                ['picking_type_id'], ['picking_type_id'])
            count = {
                x['picking_type_id'][0]: x['picking_type_id_count']
                for x in data if x['picking_type_id']
            }
            for record in self:
                record[field] = count.get(record.id, 0)

    @api.multi
    def copy_data(self, default=None):
        if default is None:
            default = {}
        default['name'] = self.name + _(' (copy)')
        return super(OperationType, self).copy_data(default)

    _sql_constraints = [
        ('default_name_company_uniq', 'unique(name, company_id)',
         'The name of the tools operation type must be unique in company!'),
    ]

    def _get_action(self, action_xmlid):
        # TDE TODO check to have one view + custo in methods
        action = self.env.ref(action_xmlid).read()[0]
        if self:
            action['display_name'] = self.display_name
        return action

    def get_action_picking_tree_draft(self):
        return self._get_action('l10n_cu_tools.action_tools_picking_tree_draft')

    def get_action_picking_tree_Confirmed(self):
        return self._get_action('l10n_cu_tools.action_tools_picking_tree_account')

    def get_action_picking_tree_done(self):
        return self._get_action('l10n_cu_tools.action_tools_picking_tree_done')

    def get_action_picking_tree_cancel(self):
        return self._get_action('l10n_cu_tools.action_tools_picking_tree_cancel')

    def get_tools_picking_action_picking_type(self):
        return self._get_action('l10n_cu_tools.action_tools_picking_tree')


