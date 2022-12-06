# -*- coding: utf-8 -*-

# Part of Desoft. See LICENSE file for full copyright and licensing details.

# List of contributors:
# Bernardo Justiz González bernardo.justiz@cmw.desoft.cu
{
    'name': "Cuban - Stock Tools Integration",
    'version': '1.0',
    "author": "Empresa de Aplicaciones Informáticas (DESOFT)",
    'website': 'https://www.desoft.cu',
    "contact": 'soporte@cmw.desoft.cu',
    'category': 'Localization',
    'description': """Stock Tools Integration""",
    'depends': ['l10n_cu_tools', 'stock'],
    'data': [
        'views/tools_operation_type.xml',
        'views/stock_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': True,
}