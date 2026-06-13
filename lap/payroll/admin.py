from django.contrib import admin
# payroll/admin.py
from django.contrib import admin
from .models import (
    SalaryStructure, PayrollRun, PayrollEntry,
    PayrollAdjustment, PayrollCarryForwardAdjustment,
)

@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ['employee', 'effective_date', 'ctc', 'basic', 'net_pay', 'is_active']
    search_fields = ['employee__username', 'employee__first_name']

@admin.register(PayrollRun)
class PayrollRunAdmin(admin.ModelAdmin):
    list_display = ['month', 'year', 'period_start', 'period_end', 'status', 'processed_by', 'created_at']

@admin.register(PayrollEntry)
class PayrollEntryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'payroll_run', 'gross', 'total_deductions', 'net_pay', 'is_paid']

@admin.register(PayrollAdjustment)
class PayrollAdjustmentAdmin(admin.ModelAdmin):
    list_display = ['payroll_entry', 'type', 'amount', 'reason', 'added_by']


@admin.register(PayrollCarryForwardAdjustment)
class PayrollCarryForwardAdjustmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'source_month', 'source_year', 'amount', 'status', 'applied_entry', 'created_at']
    list_filter = ['status', 'source_year', 'source_month']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name', 'reason']
