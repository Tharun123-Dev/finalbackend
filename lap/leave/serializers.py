# leave/serializers.py
from rest_framework import serializers
from .models import LeaveType, LeaveBalance, LeaveRequest


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LeaveType
        fields = [
            'id', 'name', 'code', 'days_allowed',
            'applicable_to', 'carry_forward', 'max_carry_forward',
            'is_paid', 'requires_document', 'min_notice_days',
            'is_active', 'description',
        ]


class LeaveBalanceSerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source='leave_type.name',       read_only=True)
    leave_type_code = serializers.CharField(source='leave_type.code',       read_only=True)
    is_paid         = serializers.BooleanField(source='leave_type.is_paid', read_only=True)
    remaining       = serializers.ReadOnlyField()

    class Meta:
        model  = LeaveBalance
        fields = [
            'id', 'leave_type', 'leave_type_name', 'leave_type_code',
            'is_paid', 'year', 'total', 'used', 'pending', 'carried', 'remaining',
        ]


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name  = serializers.SerializerMethodField()
    emp_code       = serializers.SerializerMethodField()
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    approver_name  = serializers.SerializerMethodField()

    class Meta:
        model  = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'emp_code',
            'leave_type', 'leave_type_name',
            'start_date', 'end_date', 'days', 'session',
            'reason', 'doc_url', 'status',
            'approved_by', 'approver_name', 'approver_note',
            'applied_at', 'updated_at',
        ]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name() or obj.employee.username

    def get_emp_code(self, obj):
        try:
            return obj.employee.profile.emp_code
        except Exception:
            return ''

    def get_approver_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.get_full_name() or obj.approved_by.username
        return None