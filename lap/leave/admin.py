# leave/admin.py
from django.contrib import admin
from .models import LeaveType, LeaveBalance, LeaveRequest

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'days_allowed', 'applicable_to', 'is_paid', 'is_active']

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'year', 'total', 'used', 'pending']

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'leave_type', 'start_date', 'end_date', 'days', 'status']
    list_filter   = ['status', 'leave_type']
    search_fields = ['employee__username']