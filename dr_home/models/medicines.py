from odoo import models, fields, api

class DoctorMedicines(models.Model):
    _name = 'doctor.medicines'
    _description = 'Medicines'
    _rec_name = 'medicine_name'

    medicine_name = fields.Char(string="Medicine Name", required=True, index=True)
    description = fields.Text(string="Description")

    @api.onchange('medicine_name')
    def _onchange_medicine_name(self):
        if self.medicine_name:
            self.description = self.medicine_name
