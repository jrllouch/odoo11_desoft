# -*- coding: utf-8 -*-
{
    'name': "Cuban - Stock Account",
    'version': '1.0',
    "author": "Empresa de Aplicaciones Informáticas (DESOFT)",
    'website': 'https://www.desoft.cu',
    "contact": 'soporte@cmw.desoft.cu',
    'category': 'Uncategorized',
    'description': """
This module extends the functionalities of the stock module, allowing to generate printable reports for:
======================================================================================================== 
       - Informe de Recepción
       - Vale de Entrega o Devolución
       - Transferencia entre Almacenes
       - Conduce
       - Factura
       - Submayor de Inventario
       according to the type of movement of the products, containing the mandatory fields in line with the document Resolución No. 011/2007, Ministerio de Finanzas y Precios, 18/01/2007
""",
    'depends': ['stock_account', 'l10n_cu_account'],
    'data': [
        'security/ir.model.access.csv',
        'data/init.xml',
        'report/operation_report.xml',
        'views/stock_picking_views.xml',
        'views/package_views.xml',
        'wizard/inventory_lock_date_wizard_view.xml',
        'views/res_config_settings_views.xml',
        'wizard/stock_account_submayor_wizard_view.xml',
        'report/stock_account_submayor_wizard_template.xml',
        'report/report_stock_account_physical_inventory_.xml',
        'views/stock_account_inventory.xml',
        'report/report_stock_account_blind_inventory.xml',
        'views/stock_account_quant.xml',
        # 'views/stock_account_company.xml',
        'wizard/stock_change_product_qty_views.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': True,
}
