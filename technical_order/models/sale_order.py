from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    technical_order_id = fields.Many2one('technical.order', string='Technical Order')

    def action_confirm(self):
        if self.technical_order_id:
            for line in self.order_line:
                line.check_quantities()
        return super(SaleOrder, self).action_confirm()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def check_quantities(self):
        tech_sum = sum(
            self.order_id.order_lines.filtered(lambda l: l.product_id == self.product_id.id).mapped('quantity'))
        if self.product_uom_qty > tech_sum:
            raise ValidationError(("Quantity cannot exceed %s " % tech_sum))
        return True
