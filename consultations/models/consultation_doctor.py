from odoo import api, fields, models, _


class ConsultationDoctor(models.Model):
    _name = "consultation.doctor"
    _description = "Consultation Doctor"

    name = fields.Char(string="Consultation Name", required=True)
