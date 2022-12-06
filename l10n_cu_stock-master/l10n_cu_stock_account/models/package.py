# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Package(models.Model):
    _inherit = "stock.quant.package"

    # transportacion en contenedores
    abbr = fields.Char(string=u'Acronym')
    number = fields.Char(string=u'Number')
    seal_number = fields.Char(string=u'Seal number')
    weight = fields.Float(string=u'Weight')
    rate = fields.Char(string=u'Rate')

    #importaciones transportadas en contenedores
    consignee_name = fields.Char(
        string=u'Consignee', help="Consignee's name")
    location = fields.Char(string=u'Location')
    manifest_number = fields.Char(
        string=u'Manifiesto', help='Manifest number')
    departure = fields.Char(string=u'Departure', )
    boarding = fields.Char(string=u'Boarding', help='Boarding info')
    destination = fields.Char(string=u'Destination')
    origin = fields.Char(string=u'Origin')
