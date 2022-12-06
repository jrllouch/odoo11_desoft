# -*- coding: utf-8 -*-

# Part of Desoft. See LICENSE file for full copyright and licensing details.

# List of contributors:
# Bernardo Justiz González bernardo.justiz@cmw.desoft.cu
{
    "name": "Cuban - Tools Account",
    "version": "1.0",
    "author": "Empresa de Aplicaciones Informáticas (DESOFT)",
    'website': 'https://www.desoft.cu',
    "contact": 'soporte@cmw.desoft.cu',
    'category': 'Localization',
    'description': """Tools Account""",
    'depends': ['l10n_cu_tools', 'l10n_cu_account_accountant'],
    'data': [
        'security/ir.model.access.csv',
        'views/classifier_product_categories_account_view.xml',
        'views/res_partner_account_view.xml',
        'views/tools_custodian_views.xml',
        'views/tools_picking_view.xml',
        'views/tools_quant_views.xml',
        'views/product_views.xml',
        'wizard/tools_lock_date_wizard_view.xml',
        'views/res_config_settings_view.xml',
        'report/report_deliveryslip.xml',
        'report/report_tools_account_physical_inventory.xml'
    ],
    'demo': [
    ],
}