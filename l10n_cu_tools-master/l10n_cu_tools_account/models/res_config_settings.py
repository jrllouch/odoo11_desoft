# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import odoo.tools.float_utils as fu


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    tools_lock_date = fields.Date(string="Lock Date", related="company_id.tools_lock_date", readonly=True,
                                      help="Can't edit documents prior or equal to this date.")
    # tools_lock_date_message = fields.Text('Message', default='')
    # item_ids = fields.One2many('tools.lock.date.line', 'config_id')

    def set_tools_lock_date_wizard(self):
        view = self.env.ref('l10n_cu_tools_account.tools_lock_date_form')
        if self.tools_lock_date:
            context = {'default_tools_lock_date': self.tools_lock_date}
        else:
            context = self.env.context
        return {
            'name': _('Tools Lock Date'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tools.lock.date.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context
        }
