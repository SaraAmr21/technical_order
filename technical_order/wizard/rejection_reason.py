from odoo import api, fields, models


class RejectionReasonWizard(models.TransientModel):
    _name = 'rejection.reason.wizard'
    _description = 'Rejection Reason Wizard'

    reason_cancellation = fields.Text(string="Reason for rejection", required=True)

    def action_confirm(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            order = self.env['technical.order'].browse(active_id)
            order.write({'rejection_reason': self.reason_cancellation})

        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            order = self.env['technical.order'].browse(active_id)
            order.write(order.active_id.status)
