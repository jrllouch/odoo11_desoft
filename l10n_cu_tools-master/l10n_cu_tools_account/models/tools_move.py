# Part of Desoft. See LICENSE file for full copyright and licensing details.

# List of contributors:
# Bernardo Justiz González bernardo.justiz@cmw.desoft.cu

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ToolsMove(models.Model):
    _inherit = 'tools.move'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account')

    @api.multi
    def _get_accounting_data_for_valuation(self):
        """ Return the accounts and journal to use to post Journal Entries for
        the valuation of the quant. """
        self.ensure_one()

        """"Return the expense account"""
        if self.custodian_orig_id.expense_account or self.custodian_dest_id.expense_account:
            acc_exp = self.custodian_orig_id.expense_account.id if self.custodian_orig_id.expense_account else self.custodian_dest_id.expense_account.id
        else:
            raise UserError(_(
                'Cannot find a tools expense account for the product %s. You must define one on the custodian '
                ', before processing this operation.') % (
                self.product_id.name))

        """"Return the in account"""
        if self.product_tmpl_id.categ_id.property_tool_input_account:
            acc_src = self.product_tmpl_id.categ_id.property_tool_input_account.id
        else:
            raise UserError(_(
                'Cannot find a tools input account for the product %s. You must define one on the product category, '
                'before processing this operation.') % (
                                self.product_id.name))

        """"Return the out account"""
        if self.product_tmpl_id.categ_id.property_tool_output_account:
            acc_dest = self.product_tmpl_id.categ_id.property_tool_output_account.id
        else:
            raise UserError(_(
                'Cannot find a tools output account for the product %s. You must define one on the product category, '
                'before processing this operation.') % (
                                self.product_id.name))

        """"Return the valuation account"""
        if self.product_tmpl_id.categ_id.property_tool_valoration_account:
            acc_valuation = self.product_tmpl_id.categ_id.property_tool_valoration_account.id
        else:
            raise UserError(_('You don\'t have any tools valuation account defined on your product category. '
                              'You must define one before processing this operation.'))

        """"Return the amortization account"""
        if self.product_tmpl_id.categ_id.property_tool_amortization_account:
            acc_amortization = self.product_tmpl_id.categ_id.property_tool_amortization_account.id
        else:
            raise UserError(_('You don\'t have any tools amortization account defined on your product category. '
                              'You must define one before processing this operation.'))

        """"Return the missing account"""
        if self.product_tmpl_id.categ_id.property_tool_missing_account:
            acc_missing = self.product_tmpl_id.categ_id.property_tool_missing_account.id
        else:
            raise UserError(_('You don\'t have any tools missing account defined on your product category. '
                              'You must define one before processing this operation.'))

        """"Return the surplus account"""
        if self.product_tmpl_id.categ_id.property_tool_surplus_account:
            acc_surplus = self.product_tmpl_id.categ_id.property_tool_surplus_account.id
        else:
            raise UserError(_('You don\'t have any tools surplus account defined on your product category. '
                              'You must define one before processing this operation.'))

        """"Return the tools journal"""
        if self.product_tmpl_id.categ_id.property_tool_journal:
            journal_id = self.product_tmpl_id.categ_id.property_tool_journal.id
        else:
            raise UserError(_('You don\'t have any tools journal defined on your product category, '
                              'check if you have installed a chart of accounts'))

        return journal_id, acc_src, acc_dest, acc_valuation, acc_amortization, acc_exp, acc_missing, acc_surplus

    def _account_entry_move(self):
        """ Accounting Valuation Entries """
        self.ensure_one()
        # Create Journal Entry for toools arriving in the company
        journal_id, acc_src, acc_dest, acc_valuation, acc_amortization, acc_exp, acc_missing, acc_surplus = self. \
            _get_accounting_data_for_valuation()


        if self.picking_id.picking_type_code == 'income' and self.product_tmpl_id.categ_id.\
                property_amortization_methods == '50':
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_src, acc_valuation,
                                                                                          journal_id, acc_amortization,
                                                                                          acc_exp,
                                                                                          self.analytic_account_id.id,
                                                                                          2)
        elif self.picking_id.picking_type_code == 'income' and self.product_tmpl_id.\
                categ_id.property_amortization_methods == '100in':
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_src, acc_valuation,
                                                                                          journal_id, acc_amortization,
                                                                                          acc_exp,
                                                                                          self.analytic_account_id.id,
                                                                                          1)
        elif self.picking_id.picking_type_code == 'income_surplus' and self.product_tmpl_id.categ_id.\
                property_amortization_methods == '50':
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_surplus, acc_valuation,
                                                                                          journal_id, acc_amortization,
                                                                                          acc_surplus, False, 2)
        elif self.picking_id.picking_type_code == 'income_surplus' and self.product_tmpl_id.categ_id.\
                property_amortization_methods == '100in':
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_surplus, acc_valuation,
                                                                                          journal_id, acc_amortization,
                                                                                          acc_surplus, False, 1)
        elif self.picking_id.picking_type_code == 'income_transfer' and self.product_tmpl_id.categ_id.\
                property_amortization_methods == '50':
            if self.picking_id.partner_id.property_account_tools_income_transfer_id:
                income_transfer = self.picking_id.partner_id.property_account_tools_income_transfer_id.id
            else:
                raise UserError(_('You don\'t have any tools income transfer account defined on your partner. '
                              'You must define one before processing this operation.'))
            if self.picking_id.partner_id.property_account_tools_outgoing_transfer_id:
                outgoing_transfer = self.picking_id.partner_id.property_account_tools_outgoing_transfer_id.id
            else:
                raise UserError(_('You don\'t have any tools income transfer account defined on your partner. '
                              'You must define one before processing this operation.'))
            self.with_context(force_company=self.company_id.id)._create_account_move_line(income_transfer,
                                                                                          acc_valuation,
                                                                                          journal_id, acc_amortization,
                                                                                          outgoing_transfer, False, 2)
        elif self.picking_id.picking_type_code == 'income_transfer' and self.product_tmpl_id.categ_id.\
                property_amortization_methods == '100in':
            if self.picking_id.partner_id.property_account_tools_income_transfer_id:
                income_transfer = self.picking_id.partner_id.property_account_tools_income_transfer_id.id
            else:
                raise UserError(_('You don\'t have any tools income transfer account defined on your partner. '
                              'You must define one before processing this operation.'))
            if self.picking_id.partner_id.property_account_tools_outgoing_transfer_id:
                outgoing_transfer = self.picking_id.partner_id.property_account_tools_outgoing_transfer_id.id
            else:
                raise UserError(_('You don\'t have any tools income transfer account defined on your partner. '
                              'You must define one before processing this operation.'))
            self.with_context(force_company=self.company_id.id)._create_account_move_line(income_transfer,
                                                                                          acc_valuation,
                                                                                          journal_id, acc_amortization,
                                                                                          outgoing_transfer, False, 1)
        # Create Journal Entry for tools leaving the company
        elif self.picking_id.picking_type_code == 'outgoing' and self.product_tmpl_id.categ_id.\
                property_amortization_methods == '50':
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_valuation,
                                                                                          acc_amortization,
                                                                                          journal_id, False, acc_exp,
                                                                                          self.analytic_account_id.id,
                                                                                          2, True)
        elif self.picking_id.picking_type_code == 'outgoing' and self.product_tmpl_id.\
                categ_id.property_amortization_methods == '100in':
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_valuation,
                                                                                          acc_amortization,
                                                                                          journal_id, False, False,
                                                                                          False, False)
        elif self.picking_id.picking_type_code == 'outgoing' and self.product_tmpl_id.\
                categ_id.property_amortization_methods == '100out':
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_valuation, acc_exp,
                                                                                          journal_id, False, False,
                                                                                          self.analytic_account_id.id,
                                                                                          False)
        elif self.picking_id.picking_type_code == 'outgoing_Missing' and self.product_tmpl_id.categ_id.\
                property_amortization_methods == '50':
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_valuation, acc_missing,
                                                                                          journal_id, acc_missing,
                                                                                          acc_amortization,
                                                                                          False, 2)
        elif self.picking_id.picking_type_code == 'outgoing_Missing' and self.product_tmpl_id.\
                categ_id.property_amortization_methods == '100in':
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_valuation, acc_missing,
                                                                                          journal_id, acc_missing,
                                                                                          acc_amortization, False, 1)
        elif self.picking_id.picking_type_code == 'outgoing_Missing' and self.product_tmpl_id.\
                categ_id.property_amortization_methods == '100out':
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_valuation, acc_missing,
                                                                                          journal_id, False, False,
                                                                                          False, False)
        elif self.picking_id.picking_type_code == 'outgoing_transfer' and self.product_tmpl_id.categ_id.\
                property_amortization_methods == '50':
            if self.picking_id.partner_id.property_account_tools_income_transfer_id:
                income_transfer = self.picking_id.partner_id.property_account_tools_income_transfer_id.id
            else:
                raise UserError(_('You don\'t have any tools income transfer account defined on your partner. '
                              'You must define one before processing this operation.'))
            if self.picking_id.partner_id.property_account_tools_outgoing_transfer_id:
                outgoing_transfer = self.picking_id.partner_id.property_account_tools_outgoing_transfer_id.id
            else:
                raise UserError(_('You don\'t have any tools income transfer account defined on your partner. '
                              'You must define one before processing this operation.'))
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_valuation,
                                                                                          outgoing_transfer,
                                                                                          journal_id, income_transfer,
                                                                                          acc_amortization,
                                                                                          False, 2)
        elif self.picking_id.picking_type_code == 'outgoing_transfer' and self.product_tmpl_id.\
                categ_id.property_amortization_methods == '100in':
            if self.picking_id.partner_id.property_account_tools_income_transfer_id:
                income_transfer = self.picking_id.partner_id.property_account_tools_income_transfer_id.id
            else:
                raise UserError(_('You don\'t have any tools income transfer account defined on your partner. '
                              'You must define one before processing this operation.'))
            if self.picking_id.partner_id.property_account_tools_outgoing_transfer_id:
                outgoing_transfer = self.picking_id.partner_id.property_account_tools_outgoing_transfer_id.id
            else:
                raise UserError(_('You don\'t have any tools income transfer account defined on your partner. '
                              'You must define one before processing this operation.'))
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_valuation,
                                                                                          outgoing_transfer,
                                                                                          journal_id, income_transfer,
                                                                                          acc_amortization, False, 1)
        elif self.picking_id.picking_type_code == 'outgoing_transfer' and self.product_tmpl_id.\
                categ_id.property_amortization_methods == '100out':
            if self.picking_id.partner_id.property_account_tools_income_transfer_id:
                income_transfer = self.picking_id.partner_id.property_account_tools_income_transfer_id.id
            else:
                raise UserError(_('You don\'t have any tools income transfer account defined on your partner. '
                              'You must define one before processing this operation.'))
            if self.picking_id.partner_id.property_account_tools_outgoing_transfer_id:
                outgoing_transfer = self.picking_id.partner_id.property_account_tools_outgoing_transfer_id.id
            else:
                raise UserError(_('You don\'t have any tools income transfer account defined on your partner. '
                              'You must define one before processing this operation.'))
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_valuation,
                                                                                          outgoing_transfer,
                                                                                          journal_id, False, False,
                                                                                          False, False)

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, acc_amortization=None,
                                  acc_exp=None, acc_analytic=None, methods=None, baja=None):
        self.ensure_one()
        AccountMove = self.env['account.move']
        quantity = self.env.context.get('forced_quantity', self.product_qty if self.picking_id._is_in()
                                        else -1 * self.product_qty)

        # Make an informative `ref` on the created account move to differentiate between classic
        # movements, vacuum and edition of past moves.
        ref = self.name

        if self.price_unit:
            if methods and not baja:
                move_lines = self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(
                    self.product_qty * self.price_unit), credit_account_id, debit_account_id)
                move_lines.extend(self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(
                    self.product_qty * self.price_unit/methods), acc_amortization, acc_exp, acc_analytic))
            elif methods and baja:
                move_lines = self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(
                    self.product_qty * self.price_unit/methods), False, debit_account_id)
                move_lines.extend(self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(
                    self.product_qty * self.price_unit), credit_account_id, False))
                move_lines.extend(self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(
                    self.product_qty * self.price_unit / methods), False, acc_exp, acc_analytic))
            else:
                move_lines = self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(
                    self.product_qty * self.price_unit), credit_account_id, debit_account_id)
            if move_lines:
                date = self._context.get('force_period_date', fields.Date.context_today(self))
                new_account_move = AccountMove.sudo().create({
                    'journal_id': journal_id,
                    'line_ids': move_lines,
                    'date': date,
                    'ref': ref,
                })
                new_account_move.post()

    def _prepare_account_move_line(self, qty, cost, credit_account_id=None, debit_account_id=None,
                                   analytic_account_id=None):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        self.ensure_one()

        valuation_amount = cost
        ref = self.name

        # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
        # the company currency... so we need to use round() before creating the accounting entries.
        debit_value = self.company_id.currency_id.round(valuation_amount)
        credit_value = debit_value
        res = []

        if debit_account_id:
            debit_line_vals = {
                'name': self.product_id.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': ref,
                'analytic_account_id': analytic_account_id if analytic_account_id else None,
                'debit': debit_value if debit_value > 0 else 0,
                'credit': -debit_value if debit_value < 0 else 0,
                'account_id': debit_account_id,
            }
            res.append((0, 0, debit_line_vals))
        if credit_account_id:
            credit_line_vals = {
                'name': self.product_id.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': ref,
                'credit': credit_value if credit_value > 0 else 0,
                'debit': -credit_value if credit_value < 0 else 0,
                'account_id': credit_account_id,
            }
            res.append((0, 0, credit_line_vals))
        return res
