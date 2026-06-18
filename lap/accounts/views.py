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

        if role_id:
            try:
                custom_role = CustomRole.objects.get(pk=role_id, tenant_id=tenant_id, is_active=True)
                target_role = custom_role.base_role
                target_level = custom_role.level
            except (CustomRole.DoesNotExist, ValueError, TypeError):
                target_role = None

        if not target_role:
            target_role = request.query_params.get('role') or 'employee'

        target_role = str(target_role).lower()

        from employees.access import visible_user_queryset

        qs = visible_user_queryset(request, include_self=True).exclude(id=request.query_params.get('excludeUserId') or None)

        token = getattr(request.user, '_java_token', None)
        allowed_supervisor_roles = set()
        allowed_user_emails = set()

        if token and role_id:
            try:
                from utils.java_bridge import list_role_hierarchy, list_users
                hierarchy = list_role_hierarchy(token)
                for link in hierarchy:
                    link_role_id = link.get('roleId') or link.get('role_id')
                    if str(link_role_id) == str(role_id):
                        parent_role_name = link.get('reportsToRoleName') or link.get('reports_to_role_name')
                        if parent_role_name:
                            allowed_supervisor_roles.add(str(parent_role_name).strip().upper())
                        parent_role_code = link.get('reportsToRoleCode') or link.get('reports_to_role_code')
                        if parent_role_code:
                            allowed_supervisor_roles.add(str(parent_role_code).strip().upper())
                        parent_role_id = link.get('reportsToRoleId') or link.get('reports_to_role_id')
                        if parent_role_id:
                            allowed_supervisor_roles.add(str(parent_role_id).strip().upper())

                if allowed_supervisor_roles:
                    java_users = list_users(token)
                    for ju in java_users:
                        ju_role = ju.get('role')
                        ju_role_name = ''
                        ju_role_code = ''
                        ju_role_id = ''
                        if isinstance(ju_role, dict):
                            ju_role_name = ju_role.get('name') or ''
                            ju_role_code = ju_role.get('code') or ''
                            ju_role_id = ju_role.get('id') or ''
                        else:
                            ju_role_name = ju.get('roleName') or ju.get('role') or ''
                        
                        matches = (
                            str(ju_role_name).strip().upper() in allowed_supervisor_roles or
                            str(ju_role_code).strip().upper() in allowed_supervisor_roles or
                            str(ju_role_id).strip().upper() in allowed_supervisor_roles
                        )
                        if matches:
                            email = ju.get('email')
                            if email:
                                allowed_user_emails.add(email.lower())
            except Exception as e:
                print(f"Error fetching dynamic Java role hierarchy: {e}")

        if allowed_user_emails:
            qs = qs.filter(email__in=allowed_user_emails)
        else:
            if target_level is not None:
                qs = qs.filter(custom_role__level__lt=target_level) | qs.filter(
                    role__in=['superadmin', 'admin', 'hr', 'manager']
                )
            elif target_role in ['superadmin']:
                qs = qs.none()
            elif target_role in ['admin', 'hr']:
                qs = qs.filter(role__in=['superadmin', 'admin'])
            elif target_role == 'manager':
                qs = qs.filter(role__in=['superadmin', 'admin', 'hr'])
            else:
                qs = qs.filter(role__in=['superadmin', 'admin', 'hr', 'manager'])

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
