# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.tools import pycompat


class ToolsStorageHR(models.Model):
    _inherit = 'tools.storage'

    responsible = fields.Many2one('hr.employee')
