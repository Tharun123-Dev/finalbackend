from django.contrib import admin
from .models import Notification, SystemSetting


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'type', 'is_read', 'created_at']
    list_filter  = ['type', 'is_read']
    search_fields = ['user__username', 'title']


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'label', 'value', 'category', 'updated_at']
    list_filter  = ['category']
    search_fields = ['key', 'label']