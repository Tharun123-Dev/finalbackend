# notifications/serializers.py
from rest_framework import serializers
from .models import Notification, SystemSetting


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notification
        fields = ['id', 'title', 'body', 'type', 'is_read', 'created_at']
        read_only_fields = ['id', 'title', 'body', 'type', 'created_at']


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SystemSetting
        fields = ['id', 'key', 'value', 'value_type', 'label', 'category', 'description', 'updated_at']
        read_only_fields = ['id', 'key', 'value_type', 'label', 'category', 'description', 'updated_at']
