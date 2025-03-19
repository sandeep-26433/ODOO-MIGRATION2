{
    'name': 'Appointment Booking',
    'version': '1.0',
    'summary': 'Manage Patient Appointments',
    'sequence': 10,
    'category': 'Healthcare',
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/appointment_booking.xml',
        'views/consultation_doctor.xml',
        'data/appointment_op_number_sequence.xml',  # Ensure correct path
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

