# accounts/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db.models import Q
from .models import User, CustomRole


def get_user_java_id(user):
    return str(user.id)


def save_user_profile(user, data, tenant_id=None):
    from employees.models import EmployeeProfile
    from employees.access import _safe_designation, _safe_work_mode
    from datetime import date

    # Get profileData from request data if present
    profile_data = data.get('profileData') or {}
    if not isinstance(profile_data, dict):
        profile_data = {}

    emp_code = (
        data.get('employeeId')
        or data.get('empCode')
        or profile_data.get('emp_code')
        or profile_data.get('employeeId')
    )
    if not emp_code:
        emp_code = f"USR-{user.id}"

    if not tenant_id:
        tenant_id = user.tenant_id or 'default'

    # Retrieve or create profile
    profile, created = EmployeeProfile.objects.get_or_create(
        user=user,
        defaults={
            'tenant_id': tenant_id,
            'emp_code': emp_code,
            'joining_date': date.today(),
        }
    )

    # Update simple fields
    if tenant_id and profile.tenant_id != tenant_id:
        profile.tenant_id = tenant_id
    if emp_code and profile.emp_code != emp_code:
        profile.emp_code = emp_code

    # Phone/address
    phone = data.get('phoneNumber') or data.get('phone') or profile_data.get('phone')
    if phone is not None:
        profile.phone = phone
    address = data.get('address') or profile_data.get('address')
    if address is not None:
        profile.address = address

    # Designation / Work mode
    designation = profile_data.get('designation')
    if designation:
        profile.designation = _safe_designation(designation)
    
    work_mode = profile_data.get('work_mode') or profile_data.get('workMode')
    if work_mode:
        profile.work_mode = _safe_work_mode(work_mode)

    # Dates
    joining_date = profile_data.get('joining_date') or profile_data.get('joiningDate') or data.get('joiningDate')
    if joining_date:
        profile.joining_date = joining_date
    
    dob = profile_data.get('date_of_birth') or profile_data.get('dateOfBirth') or data.get('dateOfBirth')
    if dob:
        profile.date_of_birth = dob

    # Supervisor / Manager Resolution!
    supervisor_ref = (
        data.get('rawSupervisorUserId')
        or data.get('supervisorUserId')
        or data.get('managerId')
        or profile_data.get('rawSupervisorUserId')
        or profile_data.get('reporting_supervisor_id')
        or profile_data.get('reportingSupervisorId')
    )
    if supervisor_ref:
        manager_user = None
        # 1. Prefer Java/user-code ids because the reporting dropdown returns those ids.
        all_users = User.objects.filter(tenant_id=tenant_id).select_related('profile')
        for u in all_users:
            u_profile = getattr(u, 'profile', None)
            if u_profile and u_profile.emp_code:
                import re
                match = re.search(r'(\d+)\s*$', str(u_profile.emp_code))
                if match and str(int(match.group(1))) == str(supervisor_ref):
                    manager_user = u
                    break

        # 2. Fallback to Django User PK for local-only selectors.
        if not manager_user and str(supervisor_ref).isdigit():
            manager_user = User.objects.filter(pk=int(supervisor_ref), tenant_id=tenant_id).first()
        
        # 3. Fallback search by email/username/emp_code
        if not manager_user:
            manager_user = User.objects.filter(
                Q(username__iexact=str(supervisor_ref)) |
                Q(email__iexact=str(supervisor_ref)) |
                Q(profile__emp_code__iexact=str(supervisor_ref)),
                tenant_id=tenant_id
            ).first()

        if manager_user and manager_user.id != user.id:
            profile.manager = manager_user
    else:
        profile.manager = None

    profile.save()


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

        # Update profile dynamically
        request = self.context.get('request')
        if request and request.data:
            save_user_profile(user, request.data, tenant_id=user.tenant_id)

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

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update profile dynamically
        request = self.context.get('request')
        if request and request.data:
            save_user_profile(instance, request.data, tenant_id=instance.tenant_id)

        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['firstName'] = instance.first_name
        data['lastName'] = instance.last_name
        data['role'] = instance.get_effective_role()
        data['roleName'] = instance.get_display_role()
        data['active'] = instance.is_active

        # Access profile data if it exists
        profile = getattr(instance, 'profile', None)
        profile_data = {}
        if profile:
            data['employeeId'] = profile.emp_code
            data['empCode'] = profile.emp_code
            data['joiningDate'] = str(profile.joining_date) if profile.joining_date else None
            data['dateOfBirth'] = str(profile.date_of_birth) if profile.date_of_birth else None
            data['phoneNumber'] = profile.phone

            profile_data = {
                'emp_code': profile.emp_code,
                'employeeId': profile.emp_code,
                'joining_date': str(profile.joining_date) if profile.joining_date else None,
                'joiningDate': str(profile.joining_date) if profile.joining_date else None,
                'date_of_birth': str(profile.date_of_birth) if profile.date_of_birth else None,
                'dateOfBirth': str(profile.date_of_birth) if profile.date_of_birth else None,
                'employee_type': instance.employee_type,
                'employeeType': instance.employee_type,
                'designation': profile.designation,
                'work_mode': profile.work_mode,
                'workMode': profile.work_mode,
                'phone': profile.phone,
                'address': profile.address,
            }

            if profile.manager:
                supervisor_java_id = get_user_java_id(profile.manager)
                supervisor_name = profile.manager.get_full_name() or profile.manager.username
                data['supervisorUserId'] = supervisor_java_id
                data['supervisorName'] = supervisor_name
                data['managerName'] = supervisor_name
                
                profile_data['reporting_supervisor_id'] = supervisor_java_id
                profile_data['reportingSupervisorId'] = supervisor_java_id
                profile_data['reporting_supervisor_name'] = supervisor_name
                profile_data['reportingSupervisorName'] = supervisor_name
        
        data['profileData'] = profile_data
        return data


class CustomRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CustomRole
        fields = ['id', 'name', 'display_name', 'level', 'base_role',
                  'description', 'is_active', 'created_at']
