from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    technical_order_id = fields.Many2one('technical.order', string='Technical Order')
