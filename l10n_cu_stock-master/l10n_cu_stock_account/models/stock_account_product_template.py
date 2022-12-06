# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        print(str(res.name))
        if self.check_data(res.name, res.default_code):
            raise UserError('El producto: '.join(str(self.name)) + ',' + 'con el codigo: '.join(
                str(self.default_code))+ ', ya esta registrado en el Almacen.')
        else:
            return res

    @api.multi
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if self.check_data(self.name, self.default_code):
            raise UserError('El producto: '+ ''.join(str(self.name)) + ',' + 'con el codigo: '+ ''.join(
                str(self.default_code)) + ', ya esta registrado en el Almacen.')
        else:
            return res

    def check_data(self, name, code):
        list_products = self.env['product.template'].search([('name', '=', name), ('default_code', '=', code)])
        if len(list_products) != 1:
            return True
        else:
            return False
