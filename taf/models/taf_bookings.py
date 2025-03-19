import requests
import logging
from odoo import models, fields, api
from datetime import datetime, timezone

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_taf = fields.Char(string="XTaf ID", help="Stores the user ID from the external API")

class TafBookings(models.Model):
    _name = 'taf.bookings'
    _description = 'Taf Bookings'

    user_id = fields.Many2one('res.partner', string="User", required=True)
    x_taf = fields.Char(string="API User ID")  
    patient_name = fields.Char(string="User Name", required=True)
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone Number")
    dob = fields.Datetime(string="Date of Birth")
    age = fields.Integer(string="Age")
    health_concerns = fields.Text(string="Health Concerns") 
    status = fields.Selection([
        ('pending', 'Pending'),
        ('confirmed', 'Appointment Booked'),
        ('completed', 'Consultation Completed'),
        ('cancelled', 'Cancelled')
    ], string="Status", required=True, default="pending")

    booking_date = fields.Datetime(string="Booking Date")
    appointment_id = fields.Char(string="Appointment ID")
    res_partner_id = fields.Many2one('res.partner', string="Related Contact")

    STATUS_MAPPING = {
        'pending': 'Pending',
        'confirmed': 'Confirmed',
        'completed': 'Completed',
        'cancelled': 'Cancelled'
    }
    # appointment_type = fields.Selection([
    #     ('in-clinic', 'In-Clinic'),
    #     ('videoconsult', 'Video Consultation')
    # ], string="Appointment Type", required=True)
    doctor_name = fields.Char(string="Doctor Name") 

    # video_call_link = fields.Char(string="Video Call Link", help="Google Meet link for video consultations")
  


    @api.model
    def create(self, vals):
        """Create a new TafBookings record and automatically create an Appointment Booking"""
        record = super(TafBookings, self).create(vals)

        if record.patient_name and record.email and record.phone:
            self.env['appointment.booking'].create({
                'name': record.patient_name,
                'email': record.email,
                'phone': record.phone,
                'appointment_date': record.booking_date or fields.Date.today(),
                'patient_id': record.user_id.id,
                'state': 'booked',
                'reference_id': f'TAF-{record.user_id.id}',
            })
            _logger.info("✅ Automatically created appointment.booking record for: %s", record.patient_name)

        return record

    def write(self, vals):
        """Update status in the external API only if it changes"""
        if 'status' in vals:
            new_status = vals['status']

            # Validate status before updating
            if new_status not in self.STATUS_MAPPING:
                _logger.error("❌ Invalid status value attempted: %s", new_status)
                return False  # Prevent invalid values from being saved

            for record in self:
                old_status = record.status
                appointment_id = record.appointment_id  

                if new_status != old_status and appointment_id:
                    _logger.info("🔄 Status change detected for Appointment ID %s: %s ➝ %s", 
                                 appointment_id, old_status, new_status)

                    # Update Odoo record first
                    result = super(TafBookings, self).write(vals)

                    # Sync change to API
                    self.update_appointment_status_api(appointment_id, new_status)
                    return result

        return super(TafBookings, self).write(vals)

    def update_appointment_status_api(self, appointment_id, status):
        """Send a PUT request to update the appointment status for a specific record"""
        api_url = f"https://app-2rldzj3zza-el.a.run.app/api/appointment/{appointment_id}"
        headers = {
            "Authorization": "YOUR_API_TOKEN_HERE",
            "Content-Type": "application/json"
        }

        api_status = self.STATUS_MAPPING.get(status, 'Pending')

        payload = {"status": api_status}
        try:
            response = requests.put(api_url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                _logger.info("✅ Successfully updated Appointment ID %s to status: %s", appointment_id, api_status)
            else:
                _logger.error("❌ API Error for Appointment ID %s: %s", appointment_id, response.text)
        except requests.RequestException as e:
            _logger.error("⚠️ Network error while updating Appointment ID %s: %s", appointment_id, str(e))

    @api.model
    def fetch_and_store_users(self):
        """Fetch and store user data from API"""
        _logger.info("Cron job fetch_and_store_users started.")
        # url = "https://app-2rldzj3zza-el.a.run.app/api/appointment/list?hospital=673591b50b5b714013233be5"
        url="https://thinkayurvedafirst-v4s5vamnea-el.a.run.app/api/appointment/list?hospital=675c154a859d541a0b0aef7f"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            _logger.error("❌ Request error: %s", str(e))
            return "Failed to fetch user data due to network issues."

        data = response.json()
        users = data.get("result", [])
        _logger.info("✅ Fetched %d records.", len(users))

        status_mapping = {
            'Pending': 'pending',
            'Confirmed': 'confirmed',
            'Completed': 'completed',
            'Cancelled': 'cancelled'
        }

        for item in users:
            user_data = item.get("user", {})
            appointment_id = item.get('_id')
            booking_timestamp = item.get('bookingDate')
            health_concerns = ', '.join(item.get('healthConcerns', []))
            api_status = item.get('status', '').lower()
            # appointment_type = item.get('type', 'in-clinic')  # Default to 'in-clinic'
            doctor_name = item.get("name", "")  # Doctor Name

            # video_call_link = item.get("videoCallLink", '') if appointment_type == "videoconsult" else ''


            status = status_mapping.get(api_status, "pending")

            if not user_data:
                continue

            api_user_id = user_data.get('_id')
            if not api_user_id:
                _logger.warning("⚠️ Missing _id in user data, skipping record.")
                continue

            partner = self.env['res.partner'].search([('x_taf', '=', api_user_id)], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': f"{user_data.get('firstName', '')} {user_data.get('lastName', '')}".strip(),
                    'email': user_data.get('email'),
                    'phone': str(user_data.get('phoneNumber', '')) if user_data.get('phoneNumber') else False,
                    'customer_rank': 1,
                    'is_company': False,
                    'x_taf': api_user_id,
                })
                _logger.info("✅ Created new res.partner record: %s", user_data.get('email'))

            dob_datetime = datetime.fromtimestamp(user_data.get('dob') / 1000).replace(tzinfo=None) if user_data.get('dob') else False
            booking_datetime = datetime.fromtimestamp(booking_timestamp / 1000).replace(tzinfo=None) if booking_timestamp else False

            booking = self.env['taf.bookings'].search([
                ('user_id', '=', partner.id), 
                ('appointment_id', '=', appointment_id)
            ], limit=1)

            if not booking:
                self.env['taf.bookings'].create({
                    'user_id': partner.id,
                    'x_taf': api_user_id,
                    'patient_name': f"{user_data.get('firstName', '')} {user_data.get('lastName', '')}".strip(),
                    'email': user_data.get('email'),
                    'phone': str(user_data.get('phoneNumber', '')) if user_data.get('phoneNumber') else False,
                    'dob': dob_datetime,
                    'age': user_data.get('age'),
                    'health_concerns': health_concerns,
                    'status': status,
                    # 'appointment_type': appointment_type, 
                    'doctor_name': doctor_name, 
                    # 'video_call_link': video_call_link,
                    'booking_date': booking_datetime,
                    'appointment_id': appointment_id,
                    'res_partner_id': partner.id,
                })
                _logger.info("✅ Created taf.bookings record for user: %s", user_data.get('email'))

        return "User data fetched and stored successfully!"
