# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
import odoo.tools.float_utils as fu


class InventoryLockDateWizard(models.TransientModel):
    _name = 'inventory.lock.date.wizard'

    inventory_lock_date = fields.Date(string="Lock Date", required=True, help="Can't edit documents prior or equal to "
                                      "this date.")
    message = fields.Text('Message')
    item_ids = fields.One2many('inventory.lock.date.wizard.line', 'wizard_id')

    @api.onchange('inventory_lock_date')
    def onchange_inventory_lock_date(self):
        if self.inventory_lock_date:
            message = ''
            if self.env.user.company_id.inventory_lock_date:
                if self.inventory_lock_date < self.env.user.company_id.inventory_lock_date:
                    message += _('The new inventory lock date must be greater than the old inventory lock date: %s. ') \
                               % self.env.user.company_id.inventory_lock_date

            if self.inventory_lock_date > fields.Date.today():
                message += _('The inventory lock date must be less than today. ')

            query = """SELECT pc.id, SUM(sm.value)
                       FROM product_category AS pc LEFT JOIN product_template AS pt ON pt.categ_id = pc.id 
                            LEFT JOIN product_product AS pp ON pp.product_tmpl_id = pt.id 
                            LEFT JOIN stock_move AS sm ON pp.id = sm.product_id 
                            LEFT JOIN stock_location AS sl ON sm.location_id = sl.id 
                            LEFT JOIN stock_location AS sl2 ON sm.location_dest_id = sl2.id 
                       WHERE sm.date <= %s AND sm.state = 'done' AND 
                             ((sl.company_id IS NULL AND sl2.company_id = %s) OR 
                             (sl.company_id = %s AND sl2.company_id IS NULL)) AND 
                             ((sl.usage = 'internal' AND sl2.usage != 'internal') OR
                             (sl.usage != 'internal' AND sl2.usage = 'internal'))
                       GROUP BY pc.id
                       ORDER BY pc.id"""
            params = (self.inventory_lock_date + ' 23:59:59', self.env.user.company_id.id, self.env.user.company_id.id)
            self.env.cr.execute(query, params=params)
            res = self.env.cr.fetchall()
            prod_categ_valuation = {rec[0]: (rec[1]) for rec in res}

            prod_categ_real = self.env['product.category'].search_read([('property_valuation', '=', 'real_time')],
                                                                       ['property_stock_valuation_account_id'])

            report_obj = self.env['report.account.report_trialbalance']
            account_obj = self.env['account.account']
            prod_c_obj = self.env['product.category']
            line_ids = []
            flag = True
            precision_digits = self.env['decimal.precision'].precision_get('Account')
            for prod_categ in prod_categ_real:
                prod_c = prod_c_obj.browse(prod_categ['id'])
                c = 0
                if prod_categ['id'] in prod_categ_valuation.keys():
                    c = prod_categ_valuation[prod_categ['id']]
                account = account_obj.browse(prod_categ['property_stock_valuation_account_id'][0])
                balance = report_obj._get_accounts(account, 'all')[0]['balance']
                line_ids.append((0, 0, {'product_category': prod_c.name, 'account_id': account.id,
                                        'inventory_balance': c, 'account_balance': abs(balance)}))
                c = 0

            w = []
            for temp in line_ids:
                if w:
                    found = False
                    for e in w:
                        if e[2].get('account_id'):
                            if e[2]['account_id'] == temp[2]['account_id']:
                                e[2]['product_category'] = e[2]['product_category'] + ', ' + temp[2]['product_category']
                                e[2]['inventory_balance'] = e[2]['inventory_balance'] + temp[2]['inventory_balance']
                                found = True
                                break
                    if not found:
                        w.append((0, 0, {'account_id': temp[2]['account_id'],
                                         'product_category': temp[2]['product_category'],
                                         'inventory_balance': temp[2]['inventory_balance'],
                                         'account_balance': temp[2]['account_balance']}))
                else:
                    w.append((0, 0, {'account_id': temp[2]['account_id'],
                                     'product_category': temp[2]['product_category'],
                                     'inventory_balance': temp[2]['inventory_balance'],
                                     'account_balance': temp[2]['account_balance']}))

            dif = 0
            for temp1 in w:
                dif = fu.float_round(abs(temp1[2]['account_balance'] - temp1[2]['inventory_balance']),
                                     precision_digits)
                temp1[2]['difference'] = dif

                if not fu.float_is_zero(dif, precision_digits):
                    flag = False

            pick_count = self.env['stock.picking'].search_count([('date', '<=', self.inventory_lock_date),
                                                                 ('state', 'not in', ('done', 'cancel'))])
            if pick_count:
                message += _('There are %s stock pickings with same date or earlier than lock date that are in state '
                             'different from Done or Cancelled. ') % pick_count

            inv_count = self.env['stock.inventory'].search_count([('date', '<=', self.inventory_lock_date),
                                                                  ('state', 'not in', ('done', 'cancel'))])
            if inv_count:
                message += _('There are %s stock inventories with same date or earlier than lock date that are in state'
                             ' different from Validated or Cancelled. ') % inv_count

            if self.env.user.company_id.period_lock_date:
                if self.inventory_lock_date < self.env.user.company_id.period_lock_date:
                    message += _('The inventory lock date must be equal or greater than the lock date for '
                                 'non-advisers: %s. ') % self.env.user.company_id.period_lock_date

            if not flag:
                message += _("There are differences between the inventory amount and accounting for some product "
                             "category. Please, must resolve this before continue.")

            self.item_ids = w
            self.message = message

    @api.multi
    def set_inventory_lock_date(self):
        self.env.user.company_id.write({'inventory_lock_date': self.inventory_lock_date})
        return {'type': 'ir.actions.act_window_close'}


class InventoryLockDateWizardLine(models.TransientModel):
    _name = 'inventory.lock.date.wizard.line'

    wizard_id = fields.Many2one('inventory.lock.date.wizard')
    product_category = fields.Char('Product Category')
    account_id = fields.Many2one('account.account', 'Account')
    inventory_balance = fields.Float('According inventory')
    account_balance = fields.Float('According accounting')
    difference = fields.Float('Difference')
