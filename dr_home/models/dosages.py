from odoo import models, fields, api

class DoctorDosages(models.Model):
    _name = 'doctor.dosages'
    _description = 'Dosages'
    _rec_name = 'dosage'  # Ensures that "Dosage" is displayed in dropdowns

    dosage = fields.Char(string="Dosage", required=True, index=True)
    description = fields.Text(string="Description")

    @api.onchange('dosage')
    def _onchange_dosage(self):
        if self.dosage:
            self.description = self.dosage
