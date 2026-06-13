from django.contrib import admin
from .models import Lead, LeadForm, LeadField, LeadFieldValue, FollowUp, LeadNotification


@admin.register(LeadForm)
class LeadFormAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_active', 'created_at']
    search_fields = ['name']


@admin.register(LeadField)
class LeadFieldAdmin(admin.ModelAdmin):
    list_display = ['id', 'form', 'label', 'field_type', 'required', 'order']
    list_filter = ['form', 'field_type']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'phone', 'status', 'counselor', 'created_at']
    list_filter = ['status', 'counselor']
    search_fields = ['full_name', 'email', 'phone']


@admin.register(LeadFieldValue)
class LeadFieldValueAdmin(admin.ModelAdmin):
    list_display = ['id', 'lead', 'field', 'value']


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ['id', 'lead', 'counselor', 'scheduled_at', 'completed']
    list_filter = ['completed']


@admin.register(LeadNotification)
class LeadNotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'is_read', 'created_at']