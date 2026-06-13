# utils/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from django.shortcuts import get_object_or_404

from utils.permissions import make_permission, IsSuperAdmin, IsAuthenticatedUser
from accounts.tenant_utils import get_tenant_id
from .models import Permission, RolePermission, UserPermissionOverride
from .serializers import PermissionSerializer, UserPermissionOverrideSerializer
from accounts.models import User


class CanManagePermissions(IsSuperAdmin):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_perm_code('manage_permissions')


class PermissionListView(generics.ListAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [CanManagePermissions]


class AllRolesPermissionsView(APIView):
    """Role-level defaults used by PermissionManager and effective permission checks."""
    permission_classes = [CanManagePermissions]

    def get(self, request):
        roles = ['superadmin', 'admin', 'manager', 'hr', 'counselor', 'employee']
        permissions = Permission.objects.all().order_by('module', 'code')
        role_perms  = RolePermission.objects.select_related('permission').all()

        lookup = {}
        for rp in role_perms:
            if rp.role not in lookup:
                lookup[rp.role] = {}
            lookup[rp.role][rp.permission.code] = rp.is_granted

        result = {}
        for role in roles:
            result[role] = []
            for perm in permissions:
                result[role].append({
                    'code':       perm.code,
                    'label':      perm.label,
                    'module':     perm.module,
                    'is_granted': lookup.get(role, {}).get(perm.code, False)
                })
        return Response(result)


class UpdateRolePermissionsView(APIView):
    permission_classes = [CanManagePermissions]

    def post(self, request, role):
        # Frontend may send either {"granted": [...], "revoked": [...]}
        # or a plain list (legacy). Normalise both shapes.
        data = request.data
        if isinstance(data, list):
            # Legacy: treat the whole list as "granted", nothing revoked
            granted = data
            revoked = []
        else:
            granted = data.get('granted', [])
            revoked = data.get('revoked', [])

        for code in granted:
            try:
                perm = Permission.objects.get(code=code)
                RolePermission.objects.update_or_create(
                    role=role, permission=perm,
                    defaults={'is_granted': True}
                )
            except Permission.DoesNotExist:
                pass

        for code in revoked:
            try:
                perm = Permission.objects.get(code=code)
                RolePermission.objects.update_or_create(
                    role=role, permission=perm,
                    defaults={'is_granted': False}
                )
            except Permission.DoesNotExist:
                pass

        return Response({'message': f'Permissions updated for {role}'})


# ──────────────────────────────────────────────────────────
# PER-EMPLOYEE PERMISSION MANAGEMENT (Main logic)
# ──────────────────────────────────────────────────────────

class UserPermissionsView(APIView):
    """
    GET  /api/permissions/user/<user_id>/
         Returns ALL permissions with is_granted=True/False per employee.
         This is purely override-based — no role defaults shown.

    POST /api/permissions/user/<user_id>/
         Body: { permissions: [{code, is_granted}, ...] }
         Saves/updates all overrides for the user.
         is_granted=true  → employee gets this feature
         is_granted=false → employee does NOT get this feature
    """
    permission_classes = [CanManagePermissions]

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id, tenant_id=get_tenant_id(request))
        all_perms = Permission.objects.all().order_by('module', 'code')

        existing = {
            o.permission.code: o.is_granted
            for o in UserPermissionOverride.objects.filter(user=user).select_related('permission')
        }

        result = []
        for perm in all_perms:
            result.append({
                'code':       perm.code,
                'label':      perm.label,
                'module':     perm.module,
                'is_granted': existing.get(perm.code, False),
                'is_override': perm.code in existing,
            })

        return Response({
            'user_id':      user.id,
            'username':     user.username,
            'display_role': user.get_display_role(),
            'base_role':    user.get_effective_role(),
            'permissions':  result,
        })

    def post(self, request, user_id):
        """
        Body: { permissions: [{code, is_granted}, ...] }
        Replaces all permission overrides for this user.
        """
        user = get_object_or_404(User, pk=user_id, tenant_id=get_tenant_id(request))
        permissions_data = request.data.get('permissions', [])

        saved = 0
        for item in permissions_data:
            code = item.get('code')
            is_granted = item.get('is_granted', False)
            try:
                perm = Permission.objects.get(code=code)
                UserPermissionOverride.objects.update_or_create(
                    user=user, permission=perm,
                    defaults={
                        'is_granted': is_granted,
                        'granted_by': request.user
                    }
                )
                saved += 1
            except Permission.DoesNotExist:
                pass

        return Response({
            'message': f'Permissions saved for {user.username}',
            'permissions': user.get_permissions_list(),
        })


# ──────────────────────────────────────────────────────────
# CUSTOM ROLES CRUD
# ──────────────────────────────────────────────────────────

class CustomRoleListView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        from accounts.models import CustomRole
        roles = CustomRole.objects.filter(
            is_active=True,
            tenant_id=get_tenant_id(request),
        ).values(
            'id', 'name', 'display_name', 'level', 'base_role', 'description', 'created_at'
        )
        return Response(list(roles))

    def post(self, request):
        if not request.user.has_perm_code('manage_permissions'):
            return Response({'error': 'Permission denied'}, status=403)
        from accounts.models import CustomRole
        from accounts.serializers import CustomRoleSerializer
        ser = CustomRoleSerializer(data=request.data)
        if ser.is_valid():
            ser.save(tenant_id=get_tenant_id(request))
            return Response(ser.data, status=201)
        return Response(ser.errors, status=400)


class CustomRoleDetailView(APIView):
    permission_classes = [CanManagePermissions]

    def patch(self, request, pk):
        from accounts.models import CustomRole
        from accounts.serializers import CustomRoleSerializer
        role = get_object_or_404(CustomRole, pk=pk, tenant_id=get_tenant_id(request))
        ser = CustomRoleSerializer(role, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=400)

    def delete(self, request, pk):
        from accounts.models import CustomRole
        role = get_object_or_404(CustomRole, pk=pk, tenant_id=get_tenant_id(request))
        role.is_active = False
        role.save()
        return Response({'message': 'Role deactivated'})
