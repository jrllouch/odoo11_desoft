from odoo import fields, models, api, exceptions, _


class Warehouse(models.Model):
    _inherit = "stock.warehouse"
    conduce = fields.Many2one('stock.picking.type', 'conduce')
    transfer_between_warehouses = fields.Many2one('stock.picking.type', 'Transfer Between Warehouses')
    inventory_adjustment = fields.Many2one('stock.picking.type', 'Inventory Adjustment')

    def _get_sequence_values1(self):
        sequence_values = {}
        sequence_values = super(Warehouse, self)._get_sequence_values()
        sequence_values['conduce'] = {
            'name': self.name + ' ' + _('Sequence out'),
            'prefix': self.code + '/OUT/', 'padding': 5,
            'company_id': self.company_id.id,
        }
        sequence_values['transfer_between_warehouses'] = {
            'name': self.name + ' ' + _('Sequence internal'),
            'prefix': self.code + '/INT/', 'padding': 5,
            'company_id': self.company_id.id,
        }
        sequence_values['inventory_adjustment'] = {
            'name': self.name + ' ' + _('Sequence internal'),
            'prefix': self.code + '/INT/', 'padding': 5,
            'company_id': self.company_id.id,
        }
        return sequence_values

    def create_sequences_and_picking_types(self):
        warehouse_data = super(Warehouse, self).create_sequences_and_picking_types()

        IrSequenceSudo = self.env['ir.sequence'].sudo()
        PickingType = self.env['stock.picking.type']

        input_loc, output_loc = self._get_input_output_locations(self.reception_steps, self.delivery_steps)

        # choose the next available color for the operation types of this warehouse
        all_used_colors = [res['color'] for res in
                           PickingType.search_read([('warehouse_id', '!=', False), ('color', '!=', False)], ['color'],
                                                   order='color')]
        available_colors = [zef for zef in range(0, 12) if zef not in all_used_colors]
        color = available_colors[0] if available_colors else 0

        # suit for each warehouse: reception, internal, pick, pack, ship
        max_sequence = PickingType.search_read([('sequence', '!=', False)], ['sequence'], limit=1,
                                               order='sequence desc')
        max_sequence = max_sequence and max_sequence[0]['sequence'] or 0

        sequence_data = self._get_sequence_values1()
        # tde todo: backport sequence fix
        create_data = {
            'conduce': {
                'name': _('Conduce'),
                'code': 'outgoing',
                'use_create_lots': False,
                'use_existing_lots': True,
                'default_location_dest_id': False,
                'sequence': max_sequence + 1,
            },
            'transfer_between_warehouses': {
                'name': _('Transfer Between Warehouses'),
                'code': 'internal',
                'use_create_lots': False,
                'use_existing_lots': True,
                'default_location_src_id': self.lot_stock_id.id,
                'default_location_dest_id': self.lot_stock_id.id,
                'active': self.reception_steps != 'one_step' or self.delivery_steps != 'ship_only' or self.user_has_groups(
                    'stock.group_stock_multi_locations'),
                'sequence': max_sequence + 2,
            },
            'inventory_adjustment': {
                 'name': _('Inventory Adjustment'),
                 'code': 'internal',
                 'use_create_lots': False,
                 'use_existing_lots': True,
                 'default_location_src_id': self.lot_stock_id.id,
                 'default_location_dest_id': self.lot_stock_id.id,
                 'active': self.reception_steps != 'one_step' or self.delivery_steps != 'ship_only' or self.user_has_groups(
                     'stock.group_stock_multi_locations'),
                 'sequence': max_sequence + 3,
             },
        }
        data = self._get_picking_type_values(self.reception_steps, self.delivery_steps, self.wh_pack_stock_loc_id)
        for field_name in data:
            data[field_name].update(create_data[field_name])

        for picking_type, values in data.items():
            sequence = IrSequenceSudo.create(sequence_data[picking_type])
            values.update(warehouse_id=self.id, color=color, sequence_id=sequence.id)
            warehouse_data[picking_type] = PickingType.create(values).id
        PickingType.browse(warehouse_data['out_type_id']).write({'return_picking_type_id': warehouse_data['in_type_id']})
        PickingType.browse(warehouse_data['in_type_id']).write({'return_picking_type_id': warehouse_data['out_type_id']})
        return warehouse_data