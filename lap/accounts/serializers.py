# accounts/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.get_effective_role()
        token['is_superuser'] = user.is_superuser
        token['employee_type'] = user.employee_type
        token['tenant_id'] = user.tenant_id
        token['name'] = user.get_full_name() or user.username
        token['email'] = user.email
        token['permissions'] = user.get_permissions_list()  # from DB
        return token


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'role', 'employee_type'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'tenant_id', 'employee_type', 'is_active', 'permissions'
        ]

    def get_permissions(self, obj):
        return obj.get_permissions_list()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['role'] = instance.get_effective_role()
        return data
    
# accounts/serializers.py  (add to existing file)
from rest_framework import serializers
from .models import CustomRole


class CustomRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CustomRole
        fields = ['id', 'name', 'display_name', 'level', 'base_role',
                  'description', 'is_active', 'created_at']
