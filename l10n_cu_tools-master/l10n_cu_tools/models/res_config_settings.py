# -*- coding: utf-8 -*-

# Part of Desoft. See LICENSE file for full copyright and licensing details.

# List of contributors:
# Bernardo Justiz González bernardo.justiz@cmw.desoft.cu

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_l10n_cu_dualcurrency_tools_account = fields.Boolean("Dual currency management",
                                                               help="By checking this option, the /"
                                                                    "l10n_cu_dualcurrency_tools_account /"
                                                                    "module will be installed")
    module_l10n_cu_tools_storage = fields.Boolean("Tools Storage", help="By checking this option, the /"
                                                                                   "l10n_cu_tools_storage /"
                                                                                   "module will be installed")
    module_l10n_cu_tools_hr = fields.Boolean("Integration with Hr management", 
                                             help="By checking this option, the l10n_cu_tools_hr module /"
                                                  "will be installed")

