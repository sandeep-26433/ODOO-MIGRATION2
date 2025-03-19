import logging
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import ValidationError
import re
from datetime import date

_logger = logging.getLogger(__name__)

class AppointmentBooking(models.Model):
    _name = "appointment.booking"
    _description = "Appointment Booking"

    patient_id = fields.Many2one(
    'res.partner', 
    string="Patient", 
    required=True, 
    help="Select existing patient or create a new one via popup.",
)
    name = fields.Char(string="Patient Name", required=True)
    reference_id = fields.Char(string="Patient Reference ID",copy=False)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('others', 'Others')
    ])
    date_of_birth = fields.Date(string="Date of Birth")
    age = fields.Integer(string="Age", compute='_compute_age', store=True)
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    appointment_date = fields.Date(string="Appointment Date", required=True)
    op_number = fields.Char(string="OP Number",copy=False, default=lambda self: _('New'))
    
    department = fields.Selection([
        ('kayachikitsa', 'KAYACHIKITSA'),
        ('panchakarma', 'PANCHAKARMA'),
        ('streerogam_prasutitantra', 'STREEROGAM & PRASUTITANTRA'),
        ('kaumarabrityam', 'KAUMARABRITYAM'),
        ('shalyam', 'SHALAYAM'),
        ('shalakyam', 'SHALAKYAM'),
        ('swastavrittan', 'SWASTAVRITTAN'),
        ('emergency', 'EMERGENCY'),
        ('ip', 'IP'),
        ('counter_sales', 'COUNTER SALES')
    ], string="Department")
    consultation_doctor = fields.Many2one('consultation.doctor', string="Consultation Doctor")
    consultation_mode = fields.Selection([('online', 'Online'), ('offline', 'Offline')])
    if_online = fields.Text(string="If Online")
    referral = fields.Char(string="Referral(if Any)")
    priority = fields.Char(string="Priority")
    notes = fields.Text(string="Any Notes")

    patient_type = fields.Selection([
        ('new', 'New Patient'),
        ('old', 'Old Patient')
    ], string="Patient Type", compute="_compute_patient_type", store=True)

    state = fields.Selection([
        ('booked', 'Appointment Booked'),
        ('completed', 'Consultation Completed'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='booked', tracking=True, required=True)

    doctor_appointment_id = fields.Many2one(
        'doctor.appointments',
        string="Doctor Appointment",
        readonly=True,
        help="Automatically linked Doctor Appointment"
    )

    @api.depends('phone')
    def _compute_payment(self):
        """Set payment and currency based on phone country code."""
        for record in self:
            if record.phone == '+1':
                record.payment = 30
                record.payment_currency_id = self.env.ref('base.USD').id  # USD
            elif record.phone == '+91':
                record.payment = 500
                record.payment_currency_id = self.env.ref('base.INR').id  # INR
            else:
                record.payment = 500  # Default case
                record.payment_currency_id = self.env.ref('base.INR').id  # Default INR

    payment = fields.Integer(string="Fee", compute="_compute_payment", readonly=False)
    payment_currency_id = fields.Many2one('res.currency', string="Currency", compute="_compute_payment", store=True)

    @api.constrains('name')
    def _check_name(self):
        """Validate name: only alphabets, not empty, max length 50"""
        for record in self:
            if not record.name:
                raise ValidationError("Patient Name cannot be empty.")
            if len(record.name) > 50:
                raise ValidationError("Patient Name cannot be more than 50 characters.")
            if not re.match("^[A-Za-z ]+$", record.name):
                raise ValidationError("Patient Name must contain only alphabets.")

    # @api.constrains('phone')
    # def _validate_phone_number(self):
    #     phone_pattern = re.compile(r'^\+?[0-9]{10,15}$')  # Allows optional + followed by 10-15 digits
    #     for record in self:
    #         if not record.phone:
    #             raise ValidationError("Please enter the Phone Number")
    #         if record.phone:
    #             cleaned_phone = record.phone.replace(" ", "").strip()  # Remove any spaces
    #         if not phone_pattern.match(cleaned_phone):
    #             raise ValidationError("Phone number must contain only numbers and an optional '+' at the beginning. It should have at least 10 digits.")

    @api.constrains('age')
    def _check_age(self):
        """Validate age: only numbers between 0 and 200"""
        for record in self:
            if not isinstance(record.age, int):  # Ensures only integers are entered
                raise ValidationError("Age must be a number.")
            if record.age < 0 or record.age > 200:
                raise ValidationError("Age must be between 0 and 200.")
            
    # @api.constrains('appointment_date')
    # def _check_appointment_date(self):
    #     """Validate that appointment date is not in the past"""
    #     for record in self:
    #         if record.appointment_date and record.appointment_date < date.today():
    #             raise ValidationError("Appointment Date cannot be in the past. Please select today's date or a future date.")

    @api.constrains('email')
    def _check_email(self):
        """Validate email format"""
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        for record in self:
            if record.email and not re.match(email_regex, record.email):
                raise ValidationError("Invalid Email Address. Please enter a valid email (e.g., example@domain.com).")

    @api.depends('date_of_birth')
    def _compute_age(self):
        """Calculate age from date_of_birth."""
        for record in self:
            if record.date_of_birth:
                today = datetime.today()
                birth_date = fields.Date.from_string(record.date_of_birth)
                record.age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            else:
                record.age = 0

    @api.depends('patient_id')
    def _compute_patient_type(self):
        """Determine if the patient is new or old."""
        for record in self:
            if record.patient_id:
                previous_appointments = self.env['appointment.booking'].search_count([
                    ('patient_id', '=', record.patient_id.id),
                    ('id', '!=', record.id)
                ])
                record.patient_type = 'old' if previous_appointments > 0 else 'new'
            else:
                record.patient_type = 'new'

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        """Auto-fill patient details without auto-generating reference ID."""
        if self.patient_id:
            self.name = self.patient_id.name
            self.phone = self.patient_id.phone
            self.email = self.patient_id.email
            
            # Remove automatic reference ID generation here

    def _generate_reference_id(self, patient_id):
        """Generate a unique reference ID for a patient."""
        return f'EHH-{patient_id:06d}'

    invoice_id = fields.Many2one('account.move', string="Invoice", readonly=True)

    def action_pay_now(self):
        """Create an Invoice with the correct currency based on the country code"""
        if not self.patient_id:
            raise ValidationError("A Patient is required to create an invoice.")

        # Step 1: Determine Currency
        currency_id = self.payment_currency_id.id if self.payment_currency_id else self.env.ref('base.INR').id
        payment_amount = self.payment

        # Step 2: Create the Invoice
        invoice = self.env['account.move'].create({
            'partner_id': self.patient_id.id,
            'move_type': 'out_invoice',
            'currency_id': currency_id,  # Set currency dynamically
            'invoice_line_ids': [(0, 0, {
                'name': f"Appointment with {self.consultation_doctor.name}",
                'quantity': 1,
                'price_unit': payment_amount,
                'account_id': self.env['account.account'].search([('account_type', '=', 'income')], limit=1).id,
            })],
        })
        self.invoice_id = invoice.id  # Link invoice to the appointment

        # Step 3: Validate (Post) the Invoice
        invoice.action_post()

        # Step 4: Redirect to the Invoice Form View
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Invoice',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current',
        }
    

    @api.model
    def create(self, vals):
        """Ensure correct Reference ID and OP Number while importing or creating records."""
        if vals.get('patient_id'):
            existing_ref_id = self.env['appointment.booking'].search([
                ('patient_id', '=', vals['patient_id'])
            ], limit=1).reference_id
 
            # Use imported reference_id if provided, else use existing or generate new
            if not vals.get('reference_id'):
                vals['reference_id'] = existing_ref_id or self._generate_reference_id(vals['patient_id'])
 
        # Use imported OP number if provided, else generate a new one
        if not vals.get('op_number') or vals.get('op_number') == 'New':
            vals['op_number'] = self.env['ir.sequence'].next_by_code('appointment.op_number') or '0000'
 
        if vals.get('patient_id'):
            patient = self.env['res.partner'].browse(vals['patient_id'])
            vals['name'] = patient.name
 
        # Create the record
        booking = super(AppointmentBooking, self).create(vals)

        # Create associated doctor appointment
        doctor_appointment = self.env['doctor.appointments'].create({
            'booking_id': booking.id,
            'patient_id': booking.patient_id.id,
            'appointment_date': booking.appointment_date,
            'reference_id': booking.reference_id,
            'state': booking.state,
            'op_number': booking.op_number,
            'phone': booking.patient_id.phone,  # Assuming phone is stored in res.partner
            'consultation_doctor': booking.consultation_doctor.id if booking.consultation_doctor else False,
            'consultation_mode': booking.consultation_mode,
            'patient_type': booking.patient_type,  # Ensure patient_type is stored correctly

        })

        booking.doctor_appointment_id = doctor_appointment.id
        return booking

    def action_cancel(self):
        """Cancel an appointment."""
        self.write({'state': 'cancelled'})
        if self.doctor_appointment_id:
            self.doctor_appointment_id.write({'state': 'cancelled'})

    @api.model
    def sync_taf_bookings(self):
        """Sync new records from taf.bookings into appointment.booking automatically."""
        taf_bookings = self.env['taf.bookings'].search([])
        for taf in taf_bookings:
            existing_appointment = self.env['appointment.booking'].search([
                ('reference_id', '=', f'TAF-{taf.user_id.id}')
            ], limit=1)

            if not existing_appointment:
                self.create({
                    'name': taf.patient_name,
                    'email': taf.email,
                    'phone': taf.phone,
                    'appointment_date': taf.booking_date or fields.Date.today(),
                    'patient_id': taf.user_id.id,
                    'state': 'booked',
                    'reference_id': f'TAF-{taf.user_id.id}',
                })
                _logger.info("✅ Synced taf.bookings record to appointment.booking for: %s", taf.patient_name)
