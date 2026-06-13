DEFAULT_TICKET_TYPES = [
    ('technical_issue', 'Technical Issue'),
    ('billing', 'Billing'),
    ('hr_support', 'HR Support'),
    ('leave_problem', 'Leave Problem'),
    ('payroll_issue', 'Payroll Issue'),
    ('login_problem', 'Login Problem'),
    ('vendor_support', 'Vendor Support'),
    ('lms_issue', 'LMS Issue'),
    ('crm_issue', 'CRM Issue'),
    ('attendance_issue', 'Attendance Issue'),
    ('asset_request', 'Asset Request'),
    ('network_issue', 'Network Issue'),
    ('software_access', 'Software Access'),
    ('data_correction', 'Data Correction'),
    ('policy_question', 'Policy Question'),
]


def get_tenant_id(request):
    from accounts.tenant_utils import get_tenant_id as _get_tenant_id
    return _get_tenant_id(request)


def seed_default_ticket_types(tenant_id, user=None):
    from .models import SupportTicketType

    created = 0
    for code, name in DEFAULT_TICKET_TYPES:
        _, was_created = SupportTicketType.objects.get_or_create(
            tenant_id=tenant_id,
            code=code,
            defaults={'name': name, 'created_by': user},
        )
        if was_created:
            created += 1
    return created
