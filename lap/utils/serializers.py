# utils/serializers.py
from rest_framework import serializers
from .models import Permission, RolePermission


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'code', 'label', 'module', 'description']


class RolePermissionSerializer(serializers.ModelSerializer):
    permission_code = serializers.CharField(source='permission.code', read_only=True)
    permission_label = serializers.CharField(source='permission.label', read_only=True)
    permission_module = serializers.CharField(source='permission.module', read_only=True)

    class Meta:
        model = RolePermission
        fields = [
            'id', 'role', 'permission', 'permission_code',
            'permission_label', 'permission_module', 'is_granted'
        ]
# utils/serializers.py
from rest_framework import serializers
from .models import Permission, RolePermission, UserPermissionOverride


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Permission
        fields = ['id', 'code', 'label', 'module', 'description']


class RolePermissionSerializer(serializers.ModelSerializer):
    permission_code   = serializers.CharField(source='permission.code',   read_only=True)
    permission_label  = serializers.CharField(source='permission.label',  read_only=True)
    permission_module = serializers.CharField(source='permission.module', read_only=True)

    class Meta:
        model  = RolePermission
        fields = ['id', 'role', 'permission', 'permission_code',
                  'permission_label', 'permission_module', 'is_granted']


class UserPermissionOverrideSerializer(serializers.ModelSerializer):
    permission_code  = serializers.CharField(source='permission.code',  read_only=True)
    permission_label = serializers.CharField(source='permission.label', read_only=True)
    granted_by_name  = serializers.SerializerMethodField()

    class Meta:
        model  = UserPermissionOverride
        fields = ['id', 'user', 'permission', 'permission_code',
                  'permission_label', 'is_granted', 'reason', 'granted_by_name', 'created_at']

    def get_granted_by_name(self, obj):
        if obj.granted_by:
            return obj.granted_by.get_full_name() or obj.granted_by.username
        return None