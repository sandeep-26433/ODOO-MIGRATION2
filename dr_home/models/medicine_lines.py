from odoo import models, fields, api
from odoo.exceptions import ValidationError

class DoctorMedicineLines(models.Model):
    _name = 'doctor.medicine.lines'
    _description = 'Medicine Lines'

    appointment_id = fields.Many2one('doctor.appointments', string="Appointment", ondelete='cascade', required=True)
    reference_id = fields.Char(string="Patient Reference ID", readonly=True)
    medicine_id = fields.Many2one('doctor.medicines', string="Medicine", required=True)
    dosage_id = fields.Many2one('doctor.dosages', string="Dosage")
    usage = fields.Text(string="Usage")
    days = fields.Integer(string="Days", required=True, default=1)
    course = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
    ], string="Course")
    quantity = fields.Integer(string="Quantity", required=True, default=1)
    prescription_date = fields.Date(string="Prescription Date", default=fields.Date.today)

    @api.model
    def create(self, vals):
        """Ensure reference_id is copied from appointment_id before creating a record and prevent duplicate medicines."""
        if vals.get('appointment_id') and vals.get('medicine_id'):
            appointment_id = vals['appointment_id']
            medicine_id = vals['medicine_id']

            # Check if the medicine is already prescribed in this appointment
            existing_medicine = self.search([
                ('appointment_id', '=', appointment_id),
                ('medicine_id', '=', medicine_id)
            ])
            if existing_medicine:
                raise ValidationError("This medicine has already been prescribed for this appointment. Please choose a different medicine.")

            # Copy reference_id from appointment
            appointment = self.env['doctor.appointments'].browse(appointment_id)
            if appointment.exists():
                vals['reference_id'] = appointment.reference_id

        return super(DoctorMedicineLines, self).create(vals)

    def write(self, vals):
        """Prevent duplicate medicines when updating records."""
        for record in self:
            medicine_id = vals.get('medicine_id', record.medicine_id.id)
            appointment_id = record.appointment_id.id  # Keep the existing appointment_id

            existing_medicine = self.search([
                ('appointment_id', '=', appointment_id),
                ('medicine_id', '=', medicine_id),
                ('id', '!=', record.id)  # Ignore itself while checking for duplicates
            ])
            if existing_medicine:
                raise ValidationError("This medicine has already been prescribed for this appointment. Please choose another.")

        return super(DoctorMedicineLines, self).write(vals)

    @api.constrains('days', 'quantity')
    def _check_days_quantity(self):
        """Ensure that Days and Quantity are greater than 0."""
        for record in self:
            if record.days <= 0:
                raise ValidationError("Days must be greater than 0.")
            if record.quantity <= 0:
                raise ValidationError("Quantity must be greater than 0.")
