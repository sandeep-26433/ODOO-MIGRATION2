from odoo import models, fields, api

class DoctorAppointments(models.Model):
    _name = "doctor.appointments"
    _description = "Doctor Appointments"
    _order = "appointment_date desc, id desc"

    booking_id = fields.Many2one('appointment.booking', string="Appointment Booking", readonly=True)
    patient_id = fields.Many2one('res.partner', string="Patient", required=True)
    name = fields.Char(string="Patient Name", related="patient_id.name", readonly=True)
    reference_id = fields.Char(string="Patient Reference ID")
    op_number = fields.Char(string="OP Number")
    appointment_date = fields.Date(string="Appointment Date")

    # New Fields
    phone = fields.Char(string="Phone", related="patient_id.phone", readonly=True)
    consultation_doctor = fields.Many2one('consultation.doctor', string="Consultation Doctor")
    consultation_mode = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline')
    ], string="Consultation Mode", default='offline')

    patient_type = fields.Selection([
        ('new', 'New Patient'),
        ('old', 'Old Patient')
    ], string="Patient Type", compute="_compute_patient_type", store=True)

    # Complaints Section
    chief_complaint = fields.Text(string="Chief Complaint")
    associated_complaint = fields.Text(string="Associated Complaint")
    past_history = fields.Text(string="Past History")
    family_history = fields.Text(string="Family History")
    present_history = fields.Text(string="Present History")
    diagnosis = fields.Text(string="Diagnosis")
    investigations = fields.Text(string="Investigations")
    others = fields.Text(string="Others")
    panchakarma_advice = fields.Text(string="Panchakarma Advice")

    # Health Parameters
    artava = fields.Text(string="ARTAVA")
    nadi = fields.Text(string="NADI")
    agni = fields.Text(string="AGNI")
    mala = fields.Text(string="MALA")
    mutra = fields.Text(string="MUTRA")
    nidra = fields.Text(string="NIDRA")
    manas = fields.Text(string="MANAS")

    # Vitals with computed values
    htn = fields.Char(string="HTN", compute="_compute_vitals", store=True, readonly=False)
    dm = fields.Char(string="DM", compute="_compute_vitals", store=True, readonly=False)
    th = fields.Char(string="TH", compute="_compute_vitals", store=True, readonly=False)

    # Prescription
    prescribed_details = fields.Text(string="Prescription Details")
    medicine_line_ids = fields.One2many('doctor.medicine.lines', 'appointment_id', string="Prescribed Medicines")
    new_compound = fields.Char(string="New Compound")
    ingredients= fields.Char(string="Ingredients")
    diet = fields.Selection([
    ('g', 'Diet-G: Avoid Tuberous vegetables (can consume carrot and beetroot), Besan based foods, Curd (Consume Buttermilk), Non-Veg, Masala foods, Fast foods, Deep Fried Foods.'),
    ('sk', 'Diet-SK: Avoid Brinjal, Tamarind, Fast foods, Masala foods, Deep fried foods, Curd (can consume buttermilk), Non-Veg, Besan based food.'),
    ('n', 'Diet-N: Avoid cold, refrigerated foods, Tomato, Cucumber, chocolates, ice-creams, exposure to cold winds directly, Banana, Custard apple, Consume Luke warm water.'),
    ], string="Diet")

    special_note=fields.Char(string="Special Note")
     # Compute Patient Type based on Previous Appointments
    @api.depends('patient_id')
    def _compute_patient_type(self):
        """ Determine if the patient is new or old based on past appointments. """
        for record in self:
            past_appointments = self.env['doctor.appointments'].search_count([
                ('patient_id', '=', record.patient_id.id),
                ('id', '!=', record.id)
            ])
            record.patient_type = 'old' if past_appointments else 'new'

    # Attachments
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'doctor_appointments_ir_attachments_rel',
        'appointment_id', 'attachment_id',
        string="Attachments"
    )

    # Fetch previous prescriptions
    previous_medicine_line_ids = fields.One2many(
        'doctor.medicine.lines',
        compute="_compute_previous_medicine_lines",
        string="Previous Medicines"
    )

    # Status Pipeline
    state = fields.Selection([ 
        ('booked', 'Appointment Booked'),
        ('completed', 'Consultation Completed'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='booked', tracking=True)
    @api.model
    def create(self, vals):
        """Automatically set the status to 'completed' when creating a new appointment."""
        if 'state' not in vals:
            vals['state'] = 'completed'
        return super(DoctorAppointments, self).create(vals)

    def write(self, vals):
        """Ensure the status is updated to 'completed' when saving."""
        if 'state' not in vals:
            vals['state'] = 'completed'
        return super(DoctorAppointments, self).write(vals)

    # Previous Complaints List (Many2many for Flexibility)
    previous_complaints_ids = fields.Many2many(
        'doctor.appointments',
        compute="_compute_previous_complaints",
        string="Previous Complaints"
    )

    # Fetch Last Appointment History for Reference
    last_history_id = fields.Many2one(
        'doctor.appointments',
        compute="_compute_previous_history",
        string="Last Appointment History"
    )

    # Computed Field for Patient History as Direct Text (With Bold Dates)
    previous_complaints_text = fields.Html(string="Patient History", compute="_compute_previous_complaints_text")

    @api.depends('patient_id', 'appointment_date')
    def _compute_vitals(self):
        """Fetch the latest vitals (HTN, DM, TH) from previous appointments."""
        for record in self:
            # Search for the most recent appointment for the same patient and reference_id
            last_appointment = self.env['doctor.appointments'].search([
                ('patient_id', '=', record.patient_id.id),
                ('reference_id', '=', record.reference_id),
                ('appointment_date', '<', record.appointment_date)
            ], order="appointment_date desc", limit=1)

            if last_appointment:
                record.htn = last_appointment.htn
                record.dm = last_appointment.dm
                record.th = last_appointment.th
            else:
                # If no previous appointment, set the default values
                record.htn = 'Non HTN'
                record.dm = 'Non DM'
                record.th = 'Non TH'

    @api.depends('patient_id', 'appointment_date')
    def _compute_previous_complaints_text(self):
        """Generate patient history in text format with bold dates and only entered fields."""
        for record in self:
            if record.patient_id:
                past_appointments = self.env['doctor.appointments'].search([ 
                    ('patient_id', '=', record.patient_id.id),
                    ('appointment_date', '<', record.appointment_date),
                    ('id', '!=', record.id)
                ], order="appointment_date desc")

                history_text = ""
                for appointment in past_appointments:
                    entry = f"<b>Date:</b> {appointment.appointment_date}<br/>"
                    for field in ["chief_complaint", "associated_complaint", "past_history", "family_history",
                                  "present_history", "diagnosis", "investigations", "others", "panchakarma_advice",
                                  "artava", "nadi", "agni", "mala", "mutra", "nidra", "manas"]:
                        value = getattr(appointment, field)
                        if value:
                            entry += f"<b>{field.replace('_', ' ').title()}:</b> {value}<br/>"
                    history_text += entry + "<br/>"

                record.previous_complaints_text = history_text.strip()

    @api.depends('patient_id', 'appointment_date')
    def _compute_previous_complaints(self):
        """Fetch previous complaints till yesterday's date."""
        for record in self:
            if record.patient_id and record.appointment_date:
                past_appointments = self.env['doctor.appointments'].search([ 
                    ('patient_id', '=', record.patient_id.id),
                    ('appointment_date', '<', record.appointment_date),
                    ('id', '!=', record.id)
                ], order="appointment_date desc")

                record.previous_complaints_ids = [(6, 0, past_appointments.ids)]

    @api.depends('patient_id')
    def _compute_previous_history(self):
        """Fetch past history from the last appointment."""
        for record in self:
            if record.patient_id:
                last_appointment = self.env['doctor.appointments'].search([ 
                    ('patient_id', '=', record.patient_id.id),
                    ('appointment_date', '<', record.appointment_date),
                    ('id', '!=', record.id)
                ], order="appointment_date desc", limit=1)

                record.last_history_id = last_appointment

    @api.depends('patient_id', 'appointment_date')
    def _compute_previous_medicine_lines(self):
        """Fetch prescribed medicines from past appointments and set prescription_date to appointment date."""
        for record in self:
            if record.patient_id and record.appointment_date:
                # Fetch previous appointments till the current appointment date
                past_appointments = self.env['doctor.appointments'].search([ 
                    ('patient_id', '=', record.patient_id.id),
                    ('appointment_date', '<', record.appointment_date),
                    ('id', '!=', record.id)
                ], order="appointment_date desc")

                # Fetch the previous medicines
                previous_medicines = self.env['doctor.medicine.lines'].search([
                    ('appointment_id', 'in', past_appointments.ids)
                ])

                # Update prescription_date of each medicine line
                for medicine_line in previous_medicines:
                    # Set the prescription_date of each medicine line to the appointment_date
                    medicine_line.prescription_date = medicine_line.appointment_id.appointment_date

                # Assign the medicines to the field previous_medicine_line_ids
                record.previous_medicine_line_ids = [(6, 0, previous_medicines.ids)]

    # Method to show past appointments based on Patient Reference ID
    def action_show_past_appointments(self):
        past_appointments = self.env['doctor.appointments'].search([
            ('patient_id', '=', self.patient_id.id),
            ('reference_id', '=', self.reference_id),
            ('appointment_date', '<', self.appointment_date)
        ])

        # Return an action to show the past appointments in a list view
        return {
            'type': 'ir.actions.act_window',
            'name': 'Past Appointments',
            'res_model': 'doctor.appointments',
            'view_mode': 'list',
            'views': [(self.env.ref('dr_home.view_doctor_appointments_list').id, 'list')],
            'domain': [('id', 'in', past_appointments.ids)],
            'target': 'current',
        }
    
    @api.model
    def create(self, vals):
        """Prevent duplicates when importing by checking reference_id and appointment_date before creating new records."""
 
        # ✅ Check if an appointment already exists with the same reference ID and date
        existing_appointment = self.env['doctor.appointments'].search([
            ('reference_id', '=', vals.get('reference_id')),
            ('appointment_date', '=', vals.get('appointment_date'))
        ], limit=1)
 
        if existing_appointment:
            # ✅ If found, update the existing record instead of creating a new one
            update_fields = {key: vals[key] for key in vals if key not in ['id', 'reference_id', 'appointment_date']}
            existing_appointment.write(update_fields)
            return existing_appointment  # Return the existing record instead of a new one
 
        # ✅ If no match is found, create a new appointment as usual
        return super(DoctorAppointments, self).create(vals)
    

    
    
