# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
import odoo.tools.float_utils as fu


class ToolsLockDateWizard(models.TransientModel):
    _name = 'tools.lock.date.wizard'

    tools_lock_date = fields.Date(string="Lock Date", required=True, help="Can't edit documents prior or equal to "
                                      "this date.")
    message = fields.Text('Message')
    item_ids = fields.One2many('tools.lock.date.wizard.line', 'wizard_id')

    @api.onchange('tools_lock_date')
    def onchange_tools_lock_date(self):
        if self.tools_lock_date:
            message = ''
            if self.env.user.company_id.tools_lock_date:
                if self.tools_lock_date < self.env.user.company_id.tools_lock_date:
                    message += _('The new tools lock date must be greater than the old tools lock date: %s. ') \
                               % self.env.user.company_id.tools_lock_date

            if self.tools_lock_date > fields.Date.today():
                message += _('The tools lock date must be less than today. ')

            query = """SELECT pc.id, SUM(CASE WHEN tm.custodian_orig_id ISNULL THEN tm.price_unit*tm.product_qty ELSE 
                                                  -tm.price_unit*tm.product_qty END), SUM(CASE WHEN tm.custodian_orig_id 
                                                  ISNULL THEN tm.price_unit*tm.product_qty/2 ELSE -tm.price_unit*
                                                  tm.product_qty/2 END)
                               FROM product_category AS pc LEFT JOIN product_template AS pt ON pt.categ_id = pc.id 
                                LEFT JOIN product_product AS pp ON pp.product_tmpl_id = pt.id 
                                LEFT JOIN tools_move AS tm ON pp.id = tm.product_id 
                               WHERE tm.date <= %s AND tm.state = 'done' AND tm.company_id = %s AND 
                                      (tm.custodian_orig_id ISNULL OR tm.custodian_dest_id ISNULL)
                               GROUP BY pc.id
                               ORDER BY pc.id"""
            params = (self.tools_lock_date + ' 23:59:59', self.env.user.company_id.id)
            self.env.cr.execute(query, params=params)
            res = self.env.cr.fetchall()
            prod_categ_valuation = {rec[0]: (rec[1], rec[2]) for rec in res}

            prod_categ_real = self.env['product.category'].search_read([('property_tools_valuation', '=', 'automated')],
                                                                       ['property_tool_valoration_account',
                                                                        'property_tool_amortization_account'])

            report_obj = self.env['report.account.report_trialbalance']
            account_obj = self.env['account.account']
            prod_c_obj = self.env['product.category']
            line_ids = []
            flag = True
            precision_digits = self.env['decimal.precision'].precision_get('Account')
            for prod_categ in prod_categ_real:
                # for a, b in prod_categ.items():
                # if a == 'id':
                prod_c = prod_c_obj.browse(prod_categ['id'])
                c = 0
                d = 0
                if prod_categ['id'] in prod_categ_valuation.keys():
                    c = prod_categ_valuation[prod_categ['id']][0]
                    d = prod_categ_valuation[prod_categ['id']][1]

                account = account_obj.browse(prod_categ['property_tool_valoration_account'][0])
                balance = report_obj._get_accounts(account, 'all')[0]['balance']
                line_ids.append((0, 0, {'product_category': prod_c.name, 'account_id': account.id,
                                        'tools_balance': c, 'account_balance': abs(balance)}))
                c = 0

                account = account_obj.browse(prod_categ['property_tool_amortization_account'][0])
                balance = report_obj._get_accounts(account, 'all')[0]['balance']
                line_ids.append((0, 0, {'product_category': prod_c.name, 'account_id': account.id,
                                        'tools_balance': d if d else 0,
                                        'account_balance': abs(balance)}))
                d = 0

            w = []
            for temp in line_ids:
                if w:
                    if temp[2].get('account_id'):
                        found = False
                        for e in w:
                            if e[2].get('account_id'):
                                if e[2]['account_id'] == temp[2]['account_id']:
                                    e[2]['product_category'] = e[2]['product_category'] + ', ' + temp[2][
                                        'product_category']
                                    e[2]['tools_balance'] = e[2]['tools_balance'] + temp[2]['tools_balance']
                                    found = True
                                    break
                        if not found:
                            w.append((0, 0, {'account_id': temp[2]['account_id'],
                                             'product_category': temp[2]['product_category'],
                                             'tools_balance': temp[2]['tools_balance'],
                                             'account_balance': temp[2]['account_balance']}))
                else:
                    w.append((0, 0, {'account_id': temp[2]['account_id'],
                                     'product_category': temp[2]['product_category'],
                                     'tools_balance': temp[2]['tools_balance'],
                                     'account_balance': temp[2]['account_balance']}))

            dif = 0
            for temp1 in w:
                if temp1[2].get('account_id'):
                    dif = fu.float_round(abs(temp1[2]['account_balance'] - temp1[2]['tools_balance']),
                                         precision_digits)
                    temp1[2]['difference'] = dif
                if not fu.float_is_zero(dif, precision_digits):
                    flag = False

            pick_count = self.env['tools.picking'].search_count([('date', '<=', self.tools_lock_date),
                                                                 ('state', 'not in', ('done', 'cancel'))])
            if pick_count:
                message += _('There are %s tools pickings with same date or earlier than lock date that are in state '
                             'different from Done or Cancelled. ') % pick_count

            inv_count = self.env['tools.inventory'].search_count([('date', '<=', self.tools_lock_date),
                                                                  ('state', 'not in', ('done', 'cancel'))])
            if inv_count:
                message += _('There are %s tools inventories with same date or earlier than lock date that are in state'
                             ' different from Validated or Cancelled. ') % inv_count

            if self.env.user.company_id.period_lock_date:
                if self.tools_lock_date < self.env.user.company_id.period_lock_date:
                    message += _('The tools lock date must be equal or greater than the lock date for '
                                 'non-advisers: %s. ') % self.env.user.company_id.period_lock_date

            if not flag:
                message += _("There are differences between the tools amount and accounting for some product "
                             "category. Please, must resolve this before continue.")

            self.item_ids = w
            self.message = message

    @api.multi
    def set_tools_lock_date(self):
        self.env.user.company_id.write({'tools_lock_date': self.tools_lock_date})
        return {'type': 'ir.actions.act_window_close'}


class ToolsLockDateWizardLine(models.TransientModel):
    _name = 'tools.lock.date.wizard.line'

    wizard_id = fields.Many2one('tools.lock.date.wizard')
    product_category = fields.Char('Product Category')
    account_id = fields.Many2one('account.account', 'Account')
    tools_balance = fields.Float('According tools')
    account_balance = fields.Float('According accounting')
    difference = fields.Float('Difference')
