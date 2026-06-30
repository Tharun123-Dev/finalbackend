# accounts/views.py
from django.db.models import Q
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

# ✅ make_permission only — no HasPermission
from utils.permissions import make_permission, IsAuthenticatedUser
from accounts.tenant_utils import get_tenant_id
from .models import CustomRole, User
from .serializers import MyTokenObtainPairSerializer, CreateUserSerializer, UserSerializer


def _java_value(item, *keys):
    for key in keys:
        value = item.get(key) if isinstance(item, dict) else None
        if value not in (None, ''):
            return value
    return None


def _java_user_id(item):
    return str(_java_value(item, 'id', 'userId', 'user_id') or '').strip()


def _java_supervisor_id(item):
    return str(_java_value(
        item,
        'supervisorUserId',
        'supervisor_user_id',
        'reportingToUserId',
        'managerId',
        'supervisorId',
    ) or '').strip()


def _classify_role_name(value):
    normalized = str(value or '').lower().replace('-', '_').replace(' ', '_')
    if 'super' in normalized and 'admin' in normalized:
        return 'superadmin'
    if normalized in {'admin', 'tenant_admin', 'company_admin', 'platform_admin', 'system_admin'}:
        return 'admin'
    if 'hr' in normalized or 'human_resource' in normalized:
        return 'hr'
    if 'manager' in normalized or 'head' in normalized or 'director' in normalized:
        return 'manager'
    if 'team_lead' in normalized or 'teamlead' in normalized or 'teamleader' in normalized or normalized in {'tl'} or 'leader' in normalized:
        return 'team_lead'
    return 'employee'


def _allowed_supervisor_groups(target_role):
    role_group = _classify_role_name(target_role)
    if role_group == 'superadmin':
        return set()
    if role_group == 'admin':
        return {'superadmin'}
    if role_group == 'manager':
        return {'superadmin', 'admin'}
    if role_group == 'hr':
        return {'superadmin', 'admin', 'manager'}
    if role_group == 'team_lead':
        return {'superadmin', 'admin', 'hr'}
    return {'superadmin', 'admin', 'hr', 'manager', 'team_lead'}


def _java_role_label(item):
    role = item.get('role') if isinstance(item, dict) else None
    if isinstance(role, dict):
        return role.get('name') or role.get('code') or role.get('displayName') or ''
    return (
        _java_value(item, 'roleName', 'role', 'roleCode', 'authority')
        or ''
    )


def _java_profile_data(item):
    profile = item.get('profileData') if isinstance(item, dict) else None
    return profile if isinstance(profile, dict) else {}


def _java_display_name(item):
    first_name = str(_java_value(item, 'firstName', 'first_name') or '').strip()
    last_name = str(_java_value(item, 'lastName', 'last_name') or '').strip()
    full_name = f'{first_name} {last_name}'.strip()
    return full_name or str(_java_value(item, 'displayName', 'name', 'username', 'email') or 'User')


def _java_emp_code(item):
    profile_data = _java_profile_data(item)
    return str(
        _java_value(item, 'employeeId', 'emp_code', 'empCode')
        or profile_data.get('emp_code')
        or profile_data.get('employeeId')
        or ''
    ).strip()


def _java_item_to_user_option(item):
    item_id = _java_user_id(item)
    role_label = _java_role_label(item)
    profile_data = _java_profile_data(item)
    designation = str(profile_data.get('designation') or '').strip()
    emp_code = _java_emp_code(item)
    display_name = _java_display_name(item)
    return {
        'id': item_id,
        'userId': item_id,
        'name': f'{display_name} ({emp_code})' if emp_code else display_name,
        'displayName': display_name,
        'username': str(_java_value(item, 'username', 'userName', 'email') or '').strip(),
        'email': str(_java_value(item, 'email', 'username') or '').strip(),
        'role': role_label,
        'roleGroup': _classify_role_name(f'{role_label} {designation}'),
        'designation': designation,
        'employeeId': emp_code,
        'empCode': emp_code,
        'supervisorUserId': _java_supervisor_id(item) or None,
        'managerId': _java_supervisor_id(item) or None,
    }


def _active_java_users(request):
    token = getattr(request.user, '_java_token', None)
    if not token:
        return []
    try:
        from utils.java_bridge import list_users

        return [
            item for item in list_users(token)
            if isinstance(item, dict) and item.get('active', True) is not False
        ]
    except Exception as e:
        print(f"Error fetching Java users: {e}")
        return []


def _local_user_option(user):
    profile = getattr(user, 'profile', None)
    display_name = user.get_full_name() or user.username
    emp_code = getattr(profile, 'emp_code', '') or ''
    manager_id = getattr(profile, 'manager_id', None)
    return {
        'id': user.id,
        'userId': user.id,
        'name': f'{display_name} ({emp_code})' if emp_code else display_name,
        'displayName': display_name,
        'username': user.username,
        'email': user.email,
        'role': user.get_display_role(),
        'roleGroup': _classify_role_name(f'{user.get_display_role()} {getattr(profile, "designation", "")}'),
        'designation': getattr(profile, 'designation', ''),
        'employeeId': emp_code,
        'empCode': emp_code,
        'supervisorUserId': manager_id,
        'managerId': manager_id,
    }


def _local_visible_user_queryset(request, include_self=True):
    from employees.access import _sync_java_reporting_users, is_hrms_admin, is_manager_like

    _sync_java_reporting_users(request)
    tenant_id = get_tenant_id(request)
    qs = User.objects.filter(tenant_id=tenant_id, is_active=True).select_related(
        'profile', 'profile__department', 'profile__manager', 'custom_role'
    )
    user = request.user

    if is_hrms_admin(user):
        if include_self:
            return qs.order_by('first_name', 'last_name', 'username')
        return qs.exclude(id=user.id).order_by('first_name', 'last_name', 'username')

    has_reports = qs.filter(profile__manager_id=user.id).exists()
    if is_manager_like(user) or has_reports:
        seen = set()
        queue = [user.id]
        while queue:
            current_id = queue.pop(0)
            direct_ids = list(qs.filter(profile__manager_id=current_id).values_list('id', flat=True))
            for direct_id in direct_ids:
                if direct_id not in seen:
                    seen.add(direct_id)
                    queue.append(direct_id)
        if include_self:
            seen.add(user.id)
        return qs.filter(id__in=seen).order_by('first_name', 'last_name', 'username')

    if include_self:
        return qs.filter(id=user.id)
    return qs.none()


def _hierarchy_users(request):
    return [
        _local_user_option(user)
        for user in _local_visible_user_queryset(request, include_self=True)
    ]


def _sort_options(items):
    return sorted(items, key=lambda item: str(item.get('name') or '').lower())


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class CreateUserView(generics.CreateAPIView):
    serializer_class = CreateUserSerializer
    permission_classes = [make_permission('create_user')]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, tenant_id=get_tenant_id(self.request))


class ListUsersView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [make_permission('view_users')]

    def get_queryset(self):
        role = self.request.query_params.get('role')

        qs = _local_visible_user_queryset(self.request, include_self=True).order_by('-date_joined')
        if role:
            qs = qs.filter(role=role)
        return qs


class SupervisorOptionsView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        role_id = request.query_params.get('roleId') or request.query_params.get('role_id')
        tenant_id = get_tenant_id(request)
        target_role = None
        target_level = None
        token = getattr(request.user, '_java_token', None)

        if role_id:
            try:
                custom_role = CustomRole.objects.get(pk=role_id, tenant_id=tenant_id, is_active=True)
                target_role = custom_role.base_role
                target_level = custom_role.level
                # Defensive fallback: if base_role is generic 'employee', try to classify custom role's name/display_name
                if target_role == 'employee' or not target_role:
                    alt_name = custom_role.name or custom_role.display_name
                    if alt_name and _classify_role_name(alt_name) != 'employee':
                        target_role = alt_name
            except (CustomRole.DoesNotExist, ValueError, TypeError):
                target_role = None

            if not target_role and token:
                try:
                    from utils.java_bridge import _request_json, _java_api_base_url
                    base_url = _java_api_base_url()
                    roles_list = []
                    for path in ['api/roles', 'roles', 'api/auth/roles']:
                        res = _request_json(base_url, path, token, timeout=3)
                        if isinstance(res, list):
                            roles_list = res
                            break
                        if isinstance(res, dict):
                            for key in ('roles', 'data', 'content', 'items', 'results'):
                                val = res.get(key)
                                if isinstance(val, list):
                                    roles_list = val
                                    break
                            if roles_list:
                                break
                    for r in roles_list:
                        r_id = r.get('id') or r.get('roleId') or r.get('role_id')
                        if str(r_id) == str(role_id):
                            target_role = r.get('name') or r.get('roleName') or r.get('roleCode') or r.get('code')
                            break
                except Exception as e:
                    print(f"Error fetching role from Java backend: {e}")

        if not target_role:
            target_role = (
                request.query_params.get('role')
                or request.query_params.get('roleName')
                or request.query_params.get('role_name')
                or 'employee'
            )

        target_role = str(target_role).lower().strip()

        qs = _local_visible_user_queryset(request, include_self=True).exclude(id=request.query_params.get('excludeUserId') or None)

        def java_role_parts(item):
            role = item.get('role') if isinstance(item, dict) else None
            if isinstance(role, dict):
                return {
                    str(role.get('name') or '').strip().upper(),
                    str(role.get('code') or '').strip().upper(),
                    str(role.get('id') or '').strip().upper(),
                }
            return {
                str(item.get('roleName') or item.get('role') or '').strip().upper(),
                str(item.get('roleCode') or '').strip().upper(),
                str(item.get('roleId') or item.get('role_id') or '').strip().upper(),
            }

        # Supervisors are constrained by the selected user's target role.
        allowed_groups = _allowed_supervisor_groups(target_role)

        def java_name(item):
            return _java_display_name(item)

        # Django DB filtering for the current tenant only.
        q_filter = Q()
        if allowed_groups:
            q_parts = []
            if 'superadmin' in allowed_groups:
                q_parts.append(Q(role='superadmin') | Q(is_superuser=True) | Q(custom_role__base_role='superadmin'))
            if 'admin' in allowed_groups:
                q_parts.append(Q(role='admin') | Q(custom_role__base_role='admin'))
            if 'hr' in allowed_groups:
                q_parts.append(Q(role='hr') | Q(custom_role__base_role='hr'))
            if 'manager' in allowed_groups:
                q_parts.append(Q(role='manager') | Q(custom_role__base_role='manager'))
            if 'team_lead' in allowed_groups:
                q_parts.append(
                    Q(profile__designation__in=['team_lead', 'project_manager', 'hr_manager']) | 
                    Q(custom_role__base_role='team_lead')
                )
            for part in q_parts:
                q_filter = q_filter | part
        else:
            q_filter = Q(pk__in=[])

        qs = qs.filter(q_filter)

        supervisors = []
        seen = set()
        for user in qs.select_related('profile', 'custom_role').order_by('first_name', 'last_name', 'username'):
            if user.id in seen:
                continue
            seen.add(user.id)

            display_name = user.get_full_name() or user.username
            emp_code = getattr(getattr(user, 'profile', None), 'emp_code', '')
            supervisors.append({
                'id': user.id,
                'name': f'{display_name} ({emp_code})' if emp_code else display_name,
                'role': user.get_display_role(),
                'employeeId': emp_code,
                'empCode': emp_code,
                'username': user.username,
            })

        return Response(supervisors)


class UserHierarchyView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        users = _hierarchy_users(request)
        managers = [item for item in users if item.get('roleGroup') in {'superadmin', 'admin', 'manager'}]
        hrs = [item for item in users if item.get('roleGroup') == 'hr']
        employees = [item for item in users if item.get('roleGroup') not in {'superadmin', 'admin', 'manager', 'hr'}]
        links = [
            {
                'userId': item.get('userId'),
                'managerId': item.get('managerId'),
                'supervisorUserId': item.get('supervisorUserId'),
            }
            for item in users
            if item.get('managerId') or item.get('supervisorUserId')
        ]
        return Response({
            'users': _sort_options(users),
            'managers': _sort_options(managers),
            'hrs': _sort_options(hrs),
            'employees': _sort_options(employees),
            'links': links,
        })


class UserManagersView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        users = _hierarchy_users(request)
        managers = [
            item for item in users
            if item.get('roleGroup') in {'superadmin', 'admin', 'manager'}
        ]
        return Response(_sort_options(managers))


class ManagerHrsView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request, manager_id):
        manager_id = str(manager_id)
        users = _hierarchy_users(request)
        hrs = [
            item for item in users
            if item.get('roleGroup') == 'hr'
            and str(item.get('managerId') or item.get('supervisorUserId') or '') == manager_id
        ]
        if not hrs:
            hrs = [item for item in users if item.get('roleGroup') == 'hr']
        return Response(_sort_options(hrs))


class HrEmployeesView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request, hr_id):
        hr_id = str(hr_id)
        users = _hierarchy_users(request)
        employees = [
            item for item in users
            if item.get('roleGroup') not in {'superadmin', 'admin', 'manager', 'hr'}
            and str(item.get('managerId') or item.get('supervisorUserId') or '') == hr_id
        ]
        return Response(_sort_options(employees))


class TeamMembersView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request, user_id):
        user_id = str(user_id)
        users = _hierarchy_users(request)
        by_manager = {}
        for item in users:
            manager_id = str(item.get('managerId') or item.get('supervisorUserId') or '')
            if manager_id:
                by_manager.setdefault(manager_id, []).append(item)

        team = []
        seen = set()
        queue = [user_id]
        while queue:
            current_id = queue.pop(0)
            for item in by_manager.get(current_id, []):
                item_id = str(item.get('userId') or item.get('id') or '')
                if not item_id or item_id in seen:
                    continue
                seen.add(item_id)
                team.append(item)
                queue.append(item_id)
        return Response(_sort_options(team))


class MeView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UpdateUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [make_permission('edit_user')]

    def get_queryset(self):
        return _local_visible_user_queryset(self.request, include_self=True)

# ADD to accounts/views.py

class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def patch(self, request):
        user = request.user
        for f in ['first_name','last_name','email']:
            if f in request.data:
                setattr(user, f, request.data[f])
        user.save()
        try:
            p = user.profile
            for f in ['phone','address','date_of_birth']:
                if f in request.data:
                    setattr(p, f, request.data[f])
            p.save()
        except Exception:
            pass
        from .serializers import UserSerializer
        return Response(UserSerializer(user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def post(self, request):
        old = request.data.get('old_password','')
        new = request.data.get('new_password','')
        if not old or not new:
            return Response({'error':'old_password and new_password required'},status=400)
        if not request.user.check_password(old):
            return Response({'error':'Current password is incorrect'},status=400)
        if len(new) < 8:
            return Response({'error':'Min 8 characters'},status=400)
        request.user.set_password(new)
        request.user.save()
        return Response({'message':'Password changed successfully'})
