from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date, datetime, time


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_tech_offer = fields.Boolean(string="Is Technical Offer")


class TechnicalOrder(models.Model):
    _name = "technical.order"
    _description = "Store Orders"
    _rec_name = 'sequence'
    _inherit = ['mail.thread']

    sequence = fields.Char(string='Name', readonly=True, default=lambda self: _('New'))
    request_name = fields.Char(string='Request name', required=True)
    requested_by = fields.Many2one('res.partner', string='Requested by', required=True,
                                   default=lambda self: self.env.user.partner_id)
    sale_orders = fields.One2many('sale.order', 'technical_order_id', string='Sale Orders')

    status = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], default='draft', string="Status", required=True)
    rejection_reason = fields.Text(string='Rejection Reason', readonly=True)
    start_date = fields.Date(string='Start Date', default=fields.Date.context_today, required=True)
    end_date = fields.Date(string='End Date', required=True)
    customer = fields.Many2one('res.partner', string='Customer', required=True, domain=[('is_tech_offer', '=', True)])
    order_lines = fields.One2many('technical.order.line', 'order_id', string='Order Lines')
    total = fields.Float(string='Total', compute='_compute_total_order', store=True)
    so_count = fields.Integer(string='Sale Order Count', compute='_compute_so_count')

    def action_view_sale_orders(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_type': 'tree',
            'view_mode': 'tree',
            'target': 'self',
            'domain': [('id', 'in', self.sale_orders.ids)],
            'name': 'Sale Orders',
        }

    @api.depends('sale_orders')
    def _compute_so_count(self):
        for order in self:
            order.so_count = len(order.sale_orders)

    @api.model
    def create(self, vals):
        if vals.get('sequence', _('New')) == _('New'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code('technical.order') or _('New')
        return super(TechnicalOrder, self).create(vals)

    @api.depends('order_lines')
    def _compute_total_order(self):
        for order in self:
            order.total = sum(line.total for line in order.order_lines)

    def action_submit_for_approval(self):
        self.write({'status': 'to_approve'})

    def action_cancel(self):
        self.write({'status': 'cancelled'})

    def action_reset_to_draft(self):
        self.write({'status': 'draft'})

    def action_approve(self):
        self.write({'status': 'approved'})

        sale_managers_group = self.env.ref('sales_team.group_sale_manager')
        template = self.env.ref('technical_order.email_template_technical_order_approved')
        for user in sale_managers_group.users:
            if user.partner_id.email:
                template.send_mail(self.id, email_values={'email_to': user.partner_id.email}, force_send=True)
        return True

    def action_reject(self):
        self.write({'status': 'rejected'})
        return {
            'name': _('Rejection Reason'),
            'type': 'ir.actions.act_window',
            'res_model': 'rejection.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_reason_cancellation': 'Specify default value if needed',
                'active_id': self.id,
            }
        }

    def print_report(self):
        return self.env.ref('technical_order.action_report_technical_order').report_action(self)

    def create_so(self):
        self.ensure_one()

        sale_order_lines = []
        for line in self.order_lines:
            sale_order_line_vals = {
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'price_unit': line.product_id.list_price,
            }
            sale_order_lines.append((0, 0, sale_order_line_vals))

        sale_order_vals = {
            'partner_id': self.customer.id,
            'order_line': sale_order_lines,
            'date_order': self.start_date,
            'validity_date': self.end_date,
            'technical_order_id': self.id,
        }

        sale_order = self.env['sale.order'].create(sale_order_vals)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': sale_order.id,
            'target': 'current',
        }


class TechnicalOrderLine(models.Model):
    _name = 'technical.order.line'
    _description = 'Technical Order Line'

    order_id = fields.Many2one('technical.order', string='Order Reference', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    description = fields.Char(string='Description', compute='_compute_description', store=True)
    quantity = fields.Float(string='Quantity', default=1)
    price = fields.Float(string='Price', readonly=True, related='product_id.list_price')
    total = fields.Float(string='Total', compute='_compute_total', store=True)
    remaining_qty = fields.Float(compute='compute_remaining_qty')

    @api.depends('order_id.sale_orders')
    def compute_remaining_qty(self):
        for rec in self:
            so_qty = 0
            if rec.order_id.sale_orders:
                so_qty = sum(
                    rec.order_id.sale_orders.order_line.filtered(lambda l: l.product_id == rec.product_id.id).mapped(
                        'product_uom_qty'))
            rec.remaining_qty = rec.quantity - so_qty

    @api.depends('product_id')
    def _compute_description(self):
        for line in self:
            line.description = line.product_id.name

    @api.depends('quantity', 'price')
    def _compute_total(self):
        for line in self:
            line.total = line.quantity * line.price
