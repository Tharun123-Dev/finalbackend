# accounts/views.py
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

# ✅ make_permission only — no HasPermission
from utils.permissions import make_permission, IsAuthenticatedUser
from accounts.tenant_utils import get_tenant_id
from .models import CustomRole, User
from .serializers import MyTokenObtainPairSerializer, CreateUserSerializer, UserSerializer


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
        from employees.access import visible_user_queryset

        qs = visible_user_queryset(self.request, include_self=True).order_by('-date_joined')
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

        def classify_role_name(value):
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

        if role_id:
            try:
                custom_role = CustomRole.objects.get(pk=role_id, tenant_id=tenant_id, is_active=True)
                target_role = custom_role.base_role
                target_level = custom_role.level
                # Defensive fallback: if base_role is generic 'employee', try to classify custom role's name/display_name
                if target_role == 'employee' or not target_role:
                    alt_name = custom_role.name or custom_role.display_name
                    if alt_name and classify_role_name(alt_name) != 'employee':
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

        from employees.access import visible_user_queryset

        qs = visible_user_queryset(request, include_self=True).exclude(id=request.query_params.get('excludeUserId') or None)

        current_java_id = str(getattr(request.user, '_java_user_id', '') or '').strip()
        java_supervisors = []

        def java_value(item, *keys):
            for key in keys:
                value = item.get(key) if isinstance(item, dict) else None
                if value not in (None, ''):
                    return value
            return None

        def java_user_id(item):
            return str(java_value(item, 'id', 'userId', 'user_id') or '').strip()

        def java_supervisor_id(item):
            return str(java_value(
                item,
                'supervisorUserId',
                'supervisor_user_id',
                'reportingToUserId',
                'managerId',
            ) or '').strip()

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

        # Classify the target role
        classified_target = classify_role_name(target_role)

        # Define the allowed supervisor groups
        if classified_target == 'employee':
            allowed_groups = {'superadmin', 'admin', 'hr', 'manager', 'team_lead'}
        elif classified_target == 'hr':
            allowed_groups = {'superadmin', 'admin', 'manager'}
        elif classified_target == 'manager':
            allowed_groups = {'superadmin', 'admin'}
        elif classified_target == 'team_lead':
            allowed_groups = {'superadmin', 'admin', 'hr', 'manager'}
        else:
            allowed_groups = set()

        def java_name(item):
            first_name = str(java_value(item, 'firstName', 'first_name') or '').strip()
            last_name = str(java_value(item, 'lastName', 'last_name') or '').strip()
            full_name = f'{first_name} {last_name}'.strip()
            return full_name or str(java_value(item, 'displayName', 'name', 'username', 'email') or 'User')

        def scoped_java_ids(java_users):
            if getattr(request.user, '_java_is_superuser', False):
                return {java_user_id(item) for item in java_users if java_user_id(item)}
            visible = {current_java_id} if current_java_id else set()
            frontier = list(visible)
            while frontier:
                next_frontier = []
                for item in java_users:
                    item_id = java_user_id(item)
                    if not item_id or item_id in visible:
                        continue
                    if java_supervisor_id(item) in frontier:
                        visible.add(item_id)
                        next_frontier.append(item_id)
                frontier = next_frontier
            return visible

        if token:
            try:
                from utils.java_bridge import list_users
                java_users = [
                    ju for ju in list_users(token)
                    if isinstance(ju, dict) and ju.get('active', True) is not False
                ]
                visible_java_ids = scoped_java_ids(java_users)
                seen_java_ids = set()
                for ju in java_users:
                    item_id = java_user_id(ju)
                    if not item_id or item_id in seen_java_ids or item_id not in visible_java_ids:
                        continue

                    # Classify the java user's roles
                    item_roles = {classify_role_name(part) for part in java_role_parts(ju) if part}

                    # Check designation as well in profile data
                    profile_data = ju.get('profileData') or {}
                    designation = str(profile_data.get('designation') or '').strip().lower()
                    if designation in {'team_lead', 'project_manager', 'hr_manager'}:
                        item_roles.add('team_lead')

                    # Check if the java user falls into any of the allowed supervisor groups
                    has_matching_role = False
                    for r_name in item_roles:
                        if r_name in allowed_groups:
                            has_matching_role = True
                            break
                        if r_name in {'superadmin', 'admin'} and ({'superadmin', 'admin'} & allowed_groups):
                            has_matching_role = True
                            break

                    if not has_matching_role:
                        continue

                    seen_java_ids.add(item_id)
                    role_label = next((part for part in java_role_parts(ju) if part), '')
                    emp_code = (
                        ju.get('employeeId')
                        or ju.get('emp_code')
                        or profile_data.get('emp_code')
                        or profile_data.get('employeeId')
                        or ''
                    )
                    display_name = java_name(ju)
                    username = str(java_value(ju, 'username', 'userName', 'email') or '').strip()
                    java_supervisors.append({
                        'id': item_id,
                        'name': f'{display_name} ({emp_code})' if emp_code else display_name,
                        'role': role_label,
                        'employeeId': emp_code,
                        'empCode': emp_code,
                        'username': username,
                    })
            except Exception as e:
                print(f"Error fetching dynamic Java role hierarchy: {e}")

        if java_supervisors:
            return Response(sorted(java_supervisors, key=lambda item: item['name'].lower()))

        # Fallback Django DB filtering
        from django.db.models import Q
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

        # Build map of Django users to Java user IDs by matching with java_users list
        java_user_map = {}
        if token:
            try:
                from utils.java_bridge import list_users
                java_users = list_users(token)
                for ju in java_users:
                    email = (ju.get('email') or ju.get('username') or '').strip().lower()
                    jid = ju.get('id') or ju.get('userId') or ju.get('user_id')
                    if email and jid:
                        java_user_map[email] = str(jid).strip()
            except Exception as e:
                print(f"Error building java user map: {e}")

        supervisors = []
        seen = set()
        for user in qs.select_related('profile', 'custom_role').order_by('first_name', 'last_name', 'username'):
            if user.id in seen:
                continue
            seen.add(user.id)

            # Find the Java User ID
            email_key = (user.email or '').strip().lower()
            java_id_val = java_user_map.get(email_key)
            if not java_id_val:
                emp_code = getattr(getattr(user, 'profile', None), 'emp_code', '')
                if emp_code.startswith('JAVA-'):
                    java_id_val = emp_code.split('-')[1].strip()
                else:
                    java_id_val = str(user.id)

            display_name = user.get_full_name() or user.username
            emp_code = getattr(getattr(user, 'profile', None), 'emp_code', '')
            supervisors.append({
                'id': java_id_val,  # Return Java ID instead of Django PK!
                'name': f'{display_name} ({emp_code})' if emp_code else display_name,
                'role': user.get_display_role(),
                'employeeId': emp_code,
                'empCode': emp_code,
                'username': user.username,
            })

        return Response(supervisors)


class MeView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UpdateUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [make_permission('edit_user')]

    def get_queryset(self):
        from employees.access import visible_user_queryset

        return visible_user_queryset(self.request, include_self=True)

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
