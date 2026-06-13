# attendance/admin.py
from django.contrib import admin
from .models import AttendanceRecord, AttendanceRegularization, Holiday, OfficeLocation


@admin.register(OfficeLocation)
class OfficeLocationAdmin(admin.ModelAdmin):
    list_display  = ['name', 'latitude', 'longitude', 'radius_meters', 'is_active', 'updated_at']
    list_filter   = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    ordering      = ['-is_active', '-updated_at']


@admin.register(AttendanceRecord)
class AttendanceAdmin(admin.ModelAdmin):
    list_display  = [
        'employee', 'date', 'check_in', 'check_out',
        'hours_worked', 'status', 'is_wfh',
        'checkin_distance_m', 'checkout_distance_m',
    ]
    list_filter   = ['status', 'date', 'is_wfh']
    search_fields = ['employee__username', 'employee__first_name']
    readonly_fields = [
        'checkin_latitude', 'checkin_longitude', 'checkin_distance_m',
        'checkout_latitude', 'checkout_longitude', 'checkout_distance_m',
    ]


@admin.register(AttendanceRegularization)
class RegularizationAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'attendance', 'status', 'created_at']
    list_filter   = ['status']


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ['date', 'name']