from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    technical_order_id = fields.Many2one('technical.order', string='Technical Order')

    def check_quantities(self):
        for sale_order in self:
            if sale_order.technical_order_id:
                total_requested = sum(line.quantity for line in sale_order.technical_order_id.order_lines)

                total_confirmed_draft = sum(
                    line.product_uom_qty
                    for so in sale_order.technical_order_id.sale_orders.filtered(lambda so: so.state == 'draft')
                    for line in so.order_line
                )

                total_confirmed_sale = sum(
                    line.product_uom_qty
                    for so in
                    sale_order.technical_order_id.sale_orders.filtered(lambda so: so.state in ['sale', 'done'])
                    for line in so.order_line
                )

                total_confirmed = total_confirmed_draft + total_confirmed_sale

                if total_confirmed > total_requested:
                    raise ValidationError(
                        "The total quantities of confirmed sale orders exceed the "
                        "requested quantities in the technical order."
                    )

                total_so_lines = sum(
                    sum(line.product_uom_qty for line in so.order_line)
                    for so in
                    sale_order.technical_order_id.sale_orders.filtered(lambda so: so.state in ['sale', 'done'])
                )

                if total_so_lines > total_requested:
                    raise ValidationError(
                        "The total quantities of all confirmed sale orders exceed "
                        "the requested quantities in the technical order."
                    )

    def action_confirm(self):
        self.check_quantities()
        return super(SaleOrder, self).action_confirm()
