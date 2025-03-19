{
    'name': 'Doctor Home',
    'version': '1.0',
    'summary': 'Manage Doctor Appointments, Medicines, Dosages, and Medicine Lines',
    'description': """
        This module provides functionality to manage doctor appointments, medicines, dosages, and medicine lines.
        It includes list and form views for appointments and a separate view to manage medicine lines.
    """,
    'category': 'Hospital Management',
    'depends': ['base',],
    'data': [
        'security/ir.model.access.csv',
        'views/doctor_appointments_view.xml',
        'views/doctor_medicines_view.xml',
        'views/doctor_dosages_view.xml',
        'views/doctor_medicine_lines_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}
