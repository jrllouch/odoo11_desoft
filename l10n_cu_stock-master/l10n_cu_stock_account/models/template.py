# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Template(models.Model):
    _name = 'l10n_cu_stock_account.template'
    name = fields.Char()
    code = fields.Char()
    operation_type = fields.Selection([('incoming', 'Incoming'), ('outgoing', 'Outgoing'), ('internal', 'Internal')], 'Type of Operation')
    