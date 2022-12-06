# -*- coding: utf-8 -*-
# import controllers
from . import models
from . import wizard
from . import report

from odoo import SUPERUSER_ID
from odoo import api, fields, models, _

def update_category_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env['res.company'].search([])
    env['account.asset.category']._create_account_asset_category(companies)