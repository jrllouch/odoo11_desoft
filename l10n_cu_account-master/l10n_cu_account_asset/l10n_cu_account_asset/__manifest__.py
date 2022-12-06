# -*- coding: utf-8 -*-
{
    'name': "Cuban - Assets Management",
    'version': '1.0',
    "author": "Empresa de Aplicaciones Informáticas (DESOFT)",
    'website': 'https://www.desoft.cu',
    "contact": 'soporte@cmw.desoft.cu',
    'category': 'Localization',
    'summary': "Assets Management",
    'description': "Financial and accounting asset management.",
    'depends': ['l10n_cu', 'hr', 'account_asset'],
    'data': [
        'security/l10n_cu_asset_security.xml',
        'security/ir.model.access.csv',
        'wizard/l10n_cu_asset_modify_info_view.xml',
        'wizard/l10n_cu_asset_add_depreciation_view.xml',
        'wizard/l10n_cu_asset_return_asset_view.xml',
        'wizard/l10n_cu_asset_add_components_view.xml',
        'wizard/l10n_cu_asset_change_account_view.xml',
        'wizard/l10n_cu_automatic_depreciation_asset_view.xml',
        'wizard/l10n_cu_asset_success_view.xml',
        'wizard/l10n_cu_asset_close_view.xml',
        'views/templates.xml',
        'views/l10n_cu_asset_view.xml',
        'views/l10n_cu_asset_move_view.xml',
        'views/l10n_cu_asset_menuitem.xml',
        'views/res_config_view.xml',
        'l10n_cu_asset_report.xml',
        'report/l10n_cu_asset_control.xml',
        'report/l10n_cu_fully_depreciated_assets_report.xml',
        'report/l10n_cu_asset_by_area_report.xml',
        'report/l10n_cu_listed_inventory_number_report.xml',
        'report/l10n_cu_general_reparation_report.xml',
        'report/l10n_cu_high_report.xml',
        'report/l10n_cu_low_report.xml',
        'report/l10n_cu_assets_transfers_report.xml',
        'report/l10n_cu_rented_assets_report.xml',
        'report/l10n_cu_reevaluation_report.xml',
        'report/l10n_cu_account_subaccount_balances_report.xml',
        'report/l10n_cu_account_balances_report.xml',
        'report/l10n_cu_month_depreciation_report.xml',
        'report/l10n_cu_month_amortization_report.xml',
        'report/l10n_cu_sub_ledger_building_construct_report.xml',
        'report/l10n_cu_sub_ledger_animals_report.xml',
        'report/l10n_cu_sub_ledger_machinery_in_general_report.xml',
        'report/l10n_cu_sub_ledger_permanent_plant_report.xml',
        'report/l10n_cu_sub_ledger_general_report.xml',
        'report/l10n_cu_sub_ledger_furniture_others_report.xml',
        'report/l10n_cu_sub_ledger_asset_countable_report.xml',
        'report/l10n_cu_asset_move_report.xml',
        'wizard/l10n_cu_sub_ledger_countable_assistant.xml',
        'wizard/l10n_cu_asset_general_reports_view.xml',
        'data/file.yml',
        'data/l10n_cu_asset_journal_sequence.xml',
        'data/l10n_cu_asset_journal.xml',
        'data/l10n_cu_asset_categ_group.xml',
        'data/l10n_cu_template_asset_category.xml',
        'data/l10n_cu_asset_request_sequence.xml',
        'data/l10n_cu_module_asset_data.xml',
        'data/l10n_cu_move_sequence.xml',
        'data/l10n_cu_technical_state.xml',
        'data/l10n_cu_asset_month_data.xml',
        'data/l10n_cu_asset_move_category.xml',
        'data/sub_ledger_sequence.xml',
    ],
    'demo': [],
    'application': True,
    'installable': True,
    'post_init_hook': 'update_category_init_hook',
}















