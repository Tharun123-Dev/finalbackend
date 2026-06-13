# notifications/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework.permissions import BasePermission


class IsAdminOrHR(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.has_perm_code('manage_settings')
from .models import Notification, SystemSetting
from .serializers import NotificationSerializer, SystemSettingSerializer
from accounts.tenant_utils import get_tenant_id


# ─── Notification Views ──────────────────────────────────────────────────────

class MyNotificationsView(APIView):
    """GET /api/notifications/ — returns current user's notifications (latest 50)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifs = Notification.objects.filter(user=request.user)[:50]
        serializer = NotificationSerializer(notifs, many=True)
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({
            'notifications': serializer.data,
            'unread_count': unread_count,
        })


class MarkReadView(APIView):
    """POST /api/notifications/<id>/read/ — mark one notification as read."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        notif.is_read = True
        notif.save()
        return Response({'message': 'Marked as read'})


class MarkAllReadView(APIView):
    """POST /api/notifications/read-all/ — mark all user notifications as read."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': f'{updated} notifications marked as read'})


class UnreadCountView(APIView):
    """GET /api/notifications/unread-count/ — fast unread badge count."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})


class DeleteNotificationView(APIView):
    """DELETE /api/notifications/<id>/ — delete one notification."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        notif.delete()
        return Response({'message': 'Deleted'}, status=204)


# ─── System Settings Views ────────────────────────────────────────────────────

# Keys here match exactly what seed_system_settings.py and settings_helper.py use.
# This seeds only the critical keys needed on first GET — full seed is via management command.
DEFAULT_SETTINGS = [
    # Attendance — keys must match settings_helper.py
    {'key': 'work_hours_per_day',       'label': 'Work Hours Per Day',            'value': '8',          'value_type': 'integer',  'category': 'attendance', 'description': 'Standard hours per working day'},
    {'key': 'work_days_per_week',       'label': 'Work Days Per Week',            'value': '5',          'value_type': 'integer',  'category': 'attendance', 'description': 'Working days per week'},
    {'key': 'work_start_time',          'label': 'Work Start Time',               'value': '09:00',      'value_type': 'time',     'category': 'attendance', 'description': 'Shift start time (HH:MM)'},
    {'key': 'work_end_time',            'label': 'Work End Time',                 'value': '18:00',      'value_type': 'time',     'category': 'attendance', 'description': 'Shift end time (HH:MM)'},
    {'key': 'night_shift_enabled',      'label': 'Night Shift Enabled',           'value': 'false',      'value_type': 'boolean',  'category': 'attendance', 'description': 'Use separate night shift timings for night check-ins'},
    {'key': 'night_shift_start_time',   'label': 'Night Shift Start Time',        'value': '22:00',      'value_type': 'time',     'category': 'attendance', 'description': 'Night shift start time (HH:MM)'},
    {'key': 'night_shift_end_time',     'label': 'Night Shift End Time',          'value': '06:00',      'value_type': 'time',     'category': 'attendance', 'description': 'Night shift end time (HH:MM). Can be next day'},
    {'key': 'grace_period_minutes',     'label': 'Grace Period (Minutes)',        'value': '15',         'value_type': 'integer',  'category': 'attendance', 'description': 'Minutes after shift start before marking Late'},
    {'key': 'half_day_hours',           'label': 'Half-Day Threshold (Hours)',    'value': '4',          'value_type': 'decimal',  'category': 'attendance', 'description': 'Hours worked below which = half day'},
    {'key': 'late_marks_per_half_day',  'label': 'Late Marks per Half-Day LOP',  'value': '3',          'value_type': 'integer',  'category': 'attendance', 'description': 'Number of late marks that trigger 0.5 LOP deduction'},
    {'key': 'weekend_days',             'label': 'Weekend Days',                  'value': '["saturday","sunday"]', 'value_type': 'json', 'category': 'general', 'description': 'JSON list of weekend day names'},
    # Leave
  
    {'key': 'sl_doc_required_after_days','label': 'SL Certificate After (Days)', 'value': '2',          'value_type': 'integer',  'category': 'leave',      'description': 'Medical cert required after N sick days'},
    {'key': 'sandwich_rule_enabled',    'label': 'Sandwich Rule Enabled',        'value': 'true',       'value_type': 'boolean',  'category': 'leave',      'description': 'Count sandwiched weekends as leave'},
    {'key': 'el_max_carry_forward',     'label': 'Max EL Carry Forward (Days)',  'value': '45',         'value_type': 'integer',  'category': 'leave',      'description': 'Max Earned Leave days that carry forward'},
    # Payroll
    {'key': 'payroll_lock_day',         'label': 'Payroll Lock Day',             'value': '1',          'value_type': 'integer',  'category': 'payroll',    'description': 'Fixed at day 1. Payroll for a completed month can be approved and locked from the 1st of the next month.'},
    {'key': 'overtime_multiplier',      'label': 'Overtime Multiplier',          'value': '1.5',        'value_type': 'decimal',  'category': 'payroll',    'description': 'OT pay multiplier (1.5 = 1.5x hourly rate)'},
    {'key': 'basic_salary_percent',     'label': 'Basic Salary Percentage',      'value': '40',         'value_type': 'decimal',  'category': 'payroll',    'description': 'Default Basic salary percentage used when assigning salary.'},
    {'key': 'hra_percent_metro',        'label': 'HRA Metro Percentage',         'value': '50',         'value_type': 'decimal',  'category': 'payroll',    'description': 'Default HRA percentage for metro employees.'},
    {'key': 'hra_percent_nonmetro',     'label': 'HRA Non-Metro Percentage',     'value': '40',         'value_type': 'decimal',  'category': 'payroll',    'description': 'Default HRA percentage for non-metro employees.'},
    {'key': 'da_percent',               'label': 'DA Percentage',                'value': '10',         'value_type': 'decimal',  'category': 'payroll',    'description': 'Default Dearness Allowance percentage.'},
    {'key': 'pf_employee_percent',      'label': 'PF Employee Percentage',       'value': '12',         'value_type': 'decimal',  'category': 'payroll',    'description': 'Provident Fund employee deduction percentage.'},
    {'key': 'pf_employer_percent',      'label': 'PF Employer Percentage',       'value': '12',         'value_type': 'decimal',  'category': 'payroll',    'description': 'Provident Fund employer contribution percentage.'},
    {'key': 'esi_employee_percent',     'label': 'ESI Employee Percentage',      'value': '0.75',       'value_type': 'decimal',  'category': 'payroll',    'description': 'ESI employee deduction percentage.'},
    {'key': 'esi_employer_percent',     'label': 'ESI Employer Percentage',      'value': '3.25',       'value_type': 'decimal',  'category': 'payroll',    'description': 'ESI employer contribution percentage.'},
    {'key': 'esi_threshold_salary',     'label': 'ESI Wage Threshold (₹)',       'value': '21000',      'value_type': 'integer',  'category': 'payroll',    'description': 'Gross below this = ESI applicable'},
    {'key': 'tds_flat_percent_contract','label': 'TDS Flat Contract Percentage', 'value': '10',         'value_type': 'decimal',  'category': 'payroll',    'description': 'Flat TDS percentage for contract employees.'},
    {'key': 'default_transport_allowance','label': 'Default Transport Allowance','value': '1600',       'value_type': 'decimal',  'category': 'payroll',    'description': 'Default monthly transport allowance for salary assignment.'},
    {'key': 'default_medical_allowance','label': 'Default Medical Allowance',    'value': '1250',       'value_type': 'decimal',  'category': 'payroll',    'description': 'Default monthly medical allowance for salary assignment.'},
    {'key': 'default_other_allowance',  'label': 'Default Other Allowance',      'value': '0',          'value_type': 'decimal',  'category': 'payroll',    'description': 'Default monthly other allowance for salary assignment.'},
    {'key': 'working_days_per_month',   'label': 'Working Days Per Month',       'value': '22',         'value_type': 'integer',  'category': 'payroll',    'description': 'Default working days used for payroll calculations.'},
    {'key': 'pt_threshold_salary',      'label': 'PT Gross Threshold (INR)',     'value': '15000',      'value_type': 'integer',  'category': 'payroll',    'description': 'Monthly gross salary threshold for Professional Tax'},
    {'key': 'pt_below_threshold_amount','label': 'PT Below Threshold (INR)',     'value': '0',          'value_type': 'integer',  'category': 'payroll',    'description': 'Professional Tax deducted when monthly gross is below or equal to threshold'},
    {'key': 'pt_above_threshold_amount','label': 'PT Above Threshold (INR)',     'value': '200',        'value_type': 'integer',  'category': 'payroll',    'description': 'Professional Tax deducted when monthly gross is above threshold'},
    # General
   {'key': 'company_name',      'label': 'Company Name',      'value': 'My Company', 'value_type': 'string', 'category': 'general', 'description': 'Company name shown in payslip and reports.'},
   {'key': 'currency',          'label': 'Currency',          'value': 'INR',  'value_type': 'string', 'category': 'general', 'description': 'Currency symbol used in payroll and reports.'},
{'key': 'company_logo_url',  'label': 'Company Logo URL',  'value': '',     'value_type': 'string', 'category': 'general', 'description': 'Logo URL shown in payslip and email headers.'},
    {'key': 'office_latitude',         'label': 'Office Latitude',             'value': '',           'value_type': 'decimal', 'category': 'general', 'description': 'Latitude used for office check-in/check-out location validation.'},
    {'key': 'office_longitude',        'label': 'Office Longitude',            'value': '',           'value_type': 'decimal', 'category': 'general', 'description': 'Longitude used for office check-in/check-out location validation.'},
    {'key': 'office_radius_meters',    'label': 'Office Radius (Meters)',      'value': '300',        'value_type': 'integer', 'category': 'general', 'description': 'Allowed distance from office for check-in/check-out.'},
    {'key': 'timezone',                 'label': 'Timezone',                     'value': 'Asia/Kolkata','value_type': 'string',  'category': 'general',    'description': 'System timezone'},
    {'key': 'fiscal_year_start_month',  'label': 'Fiscal Year Start Month',      'value': '4',          'value_type': 'integer',  'category': 'general',    'description': 'Month fiscal year starts (4=April)'},
    {'key': 'probation_period_months',  'label': 'Probation Period Months',      'value': '6',          'value_type': 'integer',  'category': 'general',    'description': 'Default employee probation period in months.'},
]


def seed_default_settings(tenant_id='default'):
    for s in DEFAULT_SETTINGS:
        obj, _ = SystemSetting.objects.get_or_create(
            tenant_id=tenant_id,
            key=s['key'],
            defaults={
                'value':       s['value'],
                'value_type':  s.get('value_type', 'string'),
                'label':       s['label'],
                'category':    s['category'],
                'description': s['description'],
            }
        )
        if s['key'] == 'payroll_lock_day' and obj.value != '1':
            obj.value = '1'
            obj.description = s['description']
            obj.save(update_fields=['value', 'description'])
    try:
        from attendance.models import OfficeLocation
        office = OfficeLocation.objects.filter(tenant_id=tenant_id, is_active=True).first()
        if office:
            current = {
                'office_latitude': str(office.latitude),
                'office_longitude': str(office.longitude),
                'office_radius_meters': str(office.radius_meters),
            }
            for key, value in current.items():
                setting = SystemSetting.objects.filter(tenant_id=tenant_id, key=key).first()
                if setting and not str(setting.value).strip():
                    setting.value = value
                    setting.save(update_fields=['value'])
    except Exception:
        pass


def sync_office_location_from_settings(updated_by=None, tenant_id='default'):
    """
    Keep attendance.OfficeLocation in sync with General Settings.
    If latitude/longitude are blank, leave the current office record untouched.
    """
    lat = SystemSetting.objects.filter(tenant_id=tenant_id, key='office_latitude').first()
    lon = SystemSetting.objects.filter(tenant_id=tenant_id, key='office_longitude').first()
    radius = SystemSetting.objects.filter(tenant_id=tenant_id, key='office_radius_meters').first()
    if not lat or not lon or not str(lat.value).strip() or not str(lon.value).strip():
        return None

    try:
        radius_meters = int(radius.value) if radius and str(radius.value).strip() else 300
        radius_meters = max(radius_meters, 1)
        latitude = float(lat.value)
        longitude = float(lon.value)
    except (TypeError, ValueError):
        return None

    from attendance.models import OfficeLocation
    office = OfficeLocation.objects.filter(tenant_id=tenant_id, is_active=True).first()
    if not office:
        OfficeLocation.objects.filter(tenant_id=tenant_id, is_active=True).update(is_active=False)
        office = OfficeLocation.objects.create(
            tenant_id=tenant_id,
            name='Head Office',
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            is_active=True,
        )
    else:
        office.latitude = latitude
        office.longitude = longitude
        office.radius_meters = radius_meters
        office.is_active = True
        office.save(update_fields=['latitude', 'longitude', 'radius_meters', 'is_active', 'updated_at'])
    return office


class SystemSettingsView(APIView):
    """GET /api/system-settings/ — list all, POST to bulk update (Admin only)."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdminOrHR()]

    def get(self, request):
        tenant_id = get_tenant_id(request)
        seed_default_settings(tenant_id)
        settings_qs = SystemSetting.objects.filter(tenant_id=tenant_id)
        data = {}
        for s in settings_qs:
            if s.category not in data:
                data[s.category] = []
            data[s.category].append(SystemSettingSerializer(s).data)
        return Response(data)

    def post(self, request):
        """Bulk update: send { key: new_value, ... }"""
        updates = request.data  # dict of { key: value }
        updated = []
        errors = []
        tenant_id = get_tenant_id(request)
        for key, value in updates.items():
            try:
                if key == 'payroll_lock_day':
                    value = '1'
                setting = SystemSetting.objects.get(tenant_id=tenant_id, key=key)
                setting.value = str(value)
                setting.updated_by = request.user
                setting.save()
                updated.append(key)
            except SystemSetting.DoesNotExist:
                errors.append(f'{key} not found')
        if {'office_latitude', 'office_longitude', 'office_radius_meters'} & set(updated):
            sync_office_location_from_settings(request.user, tenant_id)
        return Response({'updated': updated, 'errors': errors})


class SystemSettingDetailView(APIView):
    """PATCH /api/system-settings/<key>/ — update one setting (Admin only)."""
    permission_classes = [IsAdminOrHR]

    def patch(self, request, key):
        try:
            tenant_id = get_tenant_id(request)
            setting = SystemSetting.objects.get(tenant_id=tenant_id, key=key)
        except SystemSetting.DoesNotExist:
            return Response({'error': f'Setting "{key}" not found'}, status=404)

        value = request.data.get('value')
        if value is None:
            return Response({'error': '"value" field required'}, status=400)

        if key == 'payroll_lock_day':
            value = '1'

        setting.value = str(value)
        setting.updated_by = request.user
        setting.save()
        if key in ('office_latitude', 'office_longitude', 'office_radius_meters'):
            sync_office_location_from_settings(request.user, get_tenant_id(request))
        return Response(SystemSettingSerializer(setting).data)
