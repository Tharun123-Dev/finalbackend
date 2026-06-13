from rest_framework.permissions import BasePermission
from accounts.models import User


class IsAdminUser(BasePermission):
    """Allow access only to admin/superuser users."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Check if user is superuser or has admin role
        if request.user.is_superuser:
            return True
        role = getattr(request.user, 'role', None)
        if role is None:
            return False
        role_str = str(role).lower()
        return role_str in ('admin', 'hr', 'manager')


class IsAdminOrCounselor(BasePermission):
    """Allow access to admin users and counselors."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)