# attendance/serializers.py
from rest_framework import serializers
from .models import AttendanceRecord, AttendanceRegularization, Holiday, OfficeLocation


class OfficeLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OfficeLocation
        fields = ['id', 'name', 'latitude', 'longitude', 'radius_meters', 'is_active', 'updated_at']


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    emp_code      = serializers.SerializerMethodField()
    work_mode     = serializers.SerializerMethodField()
    regularization_status = serializers.SerializerMethodField()
    has_regularization    = serializers.SerializerMethodField()

    class Meta:
        model  = AttendanceRecord
        fields = [
            'id', 'employee', 'employee_name', 'emp_code',
            'date', 'shift_type', 'check_in', 'check_out', 'check_in_at', 'check_out_at', 'hours_worked',
            'status', 'is_wfh', 'work_mode', 'ot_hours', 'note', 'is_locked',
            'regularization_status', 'has_regularization',
            'shift_start_snapshot', 'shift_end_snapshot', 'grace_minutes_snapshot',
            'standard_hours_snapshot', 'half_day_hours_snapshot', 'is_overnight_shift',
            # location fields
            'checkin_latitude', 'checkin_longitude', 'checkin_distance_m',
            'checkout_latitude', 'checkout_longitude', 'checkout_distance_m',
        ]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name() or obj.employee.username

    def get_emp_code(self, obj):
        try:
            return obj.employee.profile.emp_code
        except Exception:
            return ''

    def get_work_mode(self, obj):
        try:
            return obj.employee.profile.work_mode
        except Exception:
            return 'office'

    def get_regularization_status(self, obj):
        try:
            return obj.regularization.status
        except Exception:
            return None

    def get_has_regularization(self, obj):
        try:
            return bool(obj.regularization.status)
        except Exception:
            return False


class RegularizationSerializer(serializers.ModelSerializer):
    employee_name    = serializers.CharField(source='employee.get_full_name', read_only=True)
    emp_code         = serializers.SerializerMethodField()
    date             = serializers.DateField(source='attendance.date', read_only=True)
    shift_type       = serializers.CharField(source='attendance.shift_type', read_only=True)
    current_checkin  = serializers.TimeField(source='attendance.check_in',  read_only=True)
    current_checkout = serializers.TimeField(source='attendance.check_out', read_only=True)
    current_status   = serializers.CharField(source='attendance.status',    read_only=True)
    approver_name    = serializers.SerializerMethodField()

    class Meta:
        model  = AttendanceRegularization
        fields = [
            'id', 'attendance', 'employee', 'employee_name', 'emp_code',
            'date', 'shift_type', 'reason',
            'requested_checkin', 'requested_checkout',
            'current_checkin', 'current_checkout', 'current_status',
            'status', 'approved_by', 'approver_name', 'approver_note',
            'created_at',
        ]

    def get_emp_code(self, obj):
        try:
            return obj.employee.profile.emp_code
        except Exception:
            return ''

    def get_approver_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.get_full_name() or obj.approved_by.username
        return None


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Holiday
        fields = ['id', 'date', 'name', 'description']
