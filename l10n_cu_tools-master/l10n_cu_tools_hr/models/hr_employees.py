# -*- coding: utf-8 -*-

# Part of Desoft. See LICENSE file for full copyright and licensing details.

# List of contributors:
# Bernardo Justiz González bernardo.justiz@cmw.desoft.cu

from odoo.addons.l10n_cu_tools.models.tools_custodian import CUSTODIAN_MODEL


CUSTODIAN_MODEL.extend([
    ('hr.employee', 'Employee')
])
