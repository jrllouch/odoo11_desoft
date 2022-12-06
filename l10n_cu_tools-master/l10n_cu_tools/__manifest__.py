# -*- coding: utf-8 -*-

# Part of Desoft. See LICENSE file for full copyright and licensing details.

# List of contributors:
# Bernardo Justiz González bernardo.justiz@cmw.desoft.cu
{
    "name": "Cuban - Tools",
    "version": "1.0",
    "author": "Empresa de Aplicaciones Informáticas (DESOFT)",
    'website': 'https://www.desoft.cu',
    "contact": 'soporte@cmw.desoft.cu',
    'category': 'Localization',
    'description': """Tools""",
    'depends': ['l10n_cu_base', 'product'],
    'data': [
        'data/tools_data.xml',
        'security/l10n_cu_tools_security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_view.xml',
        'views/tools_custodian_view.xml',
        'views/tools_quant_views.xml',
        'views/product_views.xml',
        'views/tools_picking_views.xml',
        'views/operation_type_view.xml',
        'views/tools_move_views.xml',
        'wizard/tools_quantity_history.xml',
        'report/report_deliveryslip.xml',
        'report/blind_inventory_report.xml',
        'report/report_tools_physical_inventory.xml',
        'views/tools_menuitem.xml',
        'views/tools_inventory_views.xml',
    ],
    'demo': [
    ],
    'application': True,
    'installable': True,
}