# utils/permissions.py
from rest_framework.permissions import BasePermission


def make_permission(code):
    """
    Permission check order:
      1. Superadmin / Admin → always allowed.
      2. UserPermissionOverride (is_granted=True) → allowed.
      3. Everything else → denied.

    Role-level defaults (RolePermission) are intentionally NOT checked here.
    Access is purely override-based: admin must explicitly grant permissions
    to each user.
    """
    class DynamicPermission(BasePermission):
        perm_code = code

        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False
            if request.user.is_superuser or getattr(request.user, '_java_is_superuser', False):
                return True
            return request.user.has_perm_code(self.perm_code)

    DynamicPermission.__name__ = f'Permission_{code}'
    return DynamicPermission


def make_any_permission(*codes):
    class DynamicAnyPermission(BasePermission):
        perm_codes = codes

        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False
            if request.user.is_superuser or getattr(request.user, '_java_is_superuser', False):
                return True
            return any(request.user.has_perm_code(code) for code in self.perm_codes)

    DynamicAnyPermission.__name__ = 'PermissionAny_' + '_'.join(codes)
    return DynamicAnyPermission


# Alias kept for backward compat
HasPermission = make_permission


class IsAuthenticatedUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_superuser or getattr(request.user, '_java_is_superuser', False))
        )
