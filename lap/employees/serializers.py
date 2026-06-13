# employees/serializers.py
from rest_framework import serializers
from accounts.models import User
from .models import Department, EmployeeProfile


class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model  = Department
        fields = ['id', 'name', 'description', 'employee_count', 'created_at']

    def get_employee_count(self, obj):
        return obj.employees.filter(user__is_active=True).count()


class EmployeeProfileSerializer(serializers.ModelSerializer):
    # Read fields — flattened from related user
    user_id        = serializers.IntegerField(source='user.id', read_only=True)
    username       = serializers.CharField(source='user.username',       read_only=True)
    first_name     = serializers.CharField(source='user.first_name',     read_only=True)
    last_name      = serializers.CharField(source='user.last_name',      read_only=True)
    email          = serializers.CharField(source='user.email',          read_only=True)
    role           = serializers.CharField(source='user.role',           read_only=True)
    employee_type  = serializers.CharField(source='user.employee_type',  read_only=True)
    is_active      = serializers.BooleanField(source='user.is_active',   read_only=True)
    department_name = serializers.CharField(source='department.name',    read_only=True)
    manager_name   = serializers.SerializerMethodField()

    class Meta:
        model  = EmployeeProfile
        fields = [
            'id', 'user_id','emp_code', 'username', 'first_name', 'last_name',
            'email', 'role', 'employee_type', 'is_active',
            'department', 'department_name', 'designation', 'work_mode',
            'date_of_birth', 'joining_date', 'phone', 'address',
            'manager', 'manager_name',
            'bank_account', 'ifsc_code', 'pan_number',
            'is_on_probation', 'created_at',
        ]

    def get_manager_name(self, obj):
        if obj.manager:
            return obj.manager.get_full_name() or obj.manager.username
        return None

# employees/serializers.py — updated CreateEmployeeSerializer (replace class)
class CreateEmployeeSerializer(serializers.Serializer):
    # User fields
    username      = serializers.CharField()
    email         = serializers.EmailField()
    first_name    = serializers.CharField()
    last_name     = serializers.CharField()
    password      = serializers.CharField(write_only=True)
    role          = serializers.ChoiceField(choices=['superadmin', 'admin', 'manager', 'hr', 'counselor', 'employee'])
    employee_type = serializers.ChoiceField(choices=['regular', 'contract', 'parttime', 'intern'])
    custom_role   = serializers.IntegerField(required=False, allow_null=True)  # CustomRole id

    # Profile fields
    emp_code      = serializers.CharField()
    department    = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), required=False, allow_null=True
    )
    designation   = serializers.CharField(default='other')
    work_mode     = serializers.ChoiceField(
        choices=['office', 'work_from_home'], default='office', required=False
    )
    joining_date  = serializers.DateField()
    phone         = serializers.CharField(required=False, allow_blank=True)
    address       = serializers.CharField(required=False, allow_blank=True)
    manager       = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )
    date_of_birth = serializers.DateField(required=False, allow_null=True)

    # Permission overrides — list of {code, is_granted}
    permission_overrides = serializers.ListField(
        child=serializers.DictField(), required=False, default=list
    )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def validate_emp_code(self, value):
        if EmployeeProfile.objects.filter(emp_code=value).exists():
            raise serializers.ValidationError("Employee code already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def create(self, validated_data):
        from accounts.models import CustomRole
        from utils.models import Permission, UserPermissionOverride
        from notifications.utils import notify_permission

        permission_overrides = validated_data.pop('permission_overrides', [])
        custom_role_id = validated_data.pop('custom_role', None)
        created_by = validated_data.pop('created_by', None)

        user = User(
            username      = validated_data['username'],
            email         = validated_data['email'],
            first_name    = validated_data['first_name'],
            last_name     = validated_data['last_name'],
            role          = validated_data['role'],
            employee_type = validated_data['employee_type'],
            tenant_id     = getattr(created_by, 'tenant_id', 'default') or 'default',
            created_by    = created_by,
        )
        if custom_role_id:
            try:
                user.custom_role = CustomRole.objects.get(pk=custom_role_id)
            except CustomRole.DoesNotExist:
                pass
        user.set_password(validated_data['password'])
        user.save()

        EmployeeProfile.objects.create(
            user          = user,
            tenant_id     = user.tenant_id,
            emp_code      = validated_data['emp_code'],
            department    = validated_data.get('department'),
            designation   = validated_data.get('designation', 'other'),
            work_mode     = validated_data.get('work_mode', 'office'),
            joining_date  = validated_data['joining_date'],
            phone         = validated_data.get('phone', ''),
            address       = validated_data.get('address', ''),
            manager       = validated_data.get('manager'),
            date_of_birth = validated_data.get('date_of_birth'),
        )

        # Save per-employee permission overrides
        for override in permission_overrides:
            code = override.get('code')
            is_granted = override.get('is_granted', True)
            try:
                perm = Permission.objects.get(code=code)
                UserPermissionOverride.objects.create(
                    user=user, permission=perm,
                    is_granted=is_granted,
                    reason='Set at creation'
                )
            except Permission.DoesNotExist:
                pass

        notify_permission(
            perm_code='view_employees',
            title=f"New Employee Added: {user.get_full_name()}",
            body=f"{user.get_full_name()} ({user.get_display_role()}) has been added to the system.",
            notif_type='new_account'
        )

        return user
