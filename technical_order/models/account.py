from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class Account(models.Model):
    _inherit = ['account.move.line']

    size = fields.Integer(String='Size')
