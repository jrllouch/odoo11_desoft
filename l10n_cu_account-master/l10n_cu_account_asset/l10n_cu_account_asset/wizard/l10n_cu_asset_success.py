# -*- coding: utf-8 -*-
from odoo import fields, api, models, exceptions, _


class l10n_cu_AssetSuccess(models.TransientModel):
    _name = 'l10n_cu.asset.success'

    message = fields.Text('Message', readonly=True)
