# utils/models.py
from django.db import models
from django.conf import settings


class Permission(models.Model):
    MODULES = [
        ('employees',   'Employees'),
        ('departments', 'Departments'),
        ('attendance',  'Attendance'),
        ('leave',       'Leave'),
        ('payroll',     'Payroll'),
        ('reports',     'Reports'),
        ('users',       'Users'),
        ('settings',    'Settings'),
        ('notifications','Notifications'),
        ('support_tickets', 'Support Tickets'),
        ('affiliate', 'Affiliate'),
        ('leads', 'Leads'),
        ('tasks', 'Tasks'),
        ('revenue', 'Revenue'),
    ]

    code        = models.CharField(max_length=100, unique=True)
    label       = models.CharField(max_length=100)
    module      = models.CharField(max_length=50, choices=MODULES)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['module', 'code']

    def __str__(self):
        return f"{self.module} | {self.label}"


class RolePermission(models.Model):
    """Default permissions per BASE role (superadmin/admin/manager/hr/employee)."""
    ROLES = [
        ('superadmin', 'SuperAdmin'),
        ('admin',      'Admin'),
        ('manager',    'Manager'),
        ('hr',         'HR'),
        ('counselor',  'Counselor'),
        ('employee',   'Employee'),
    ]

    role       = models.CharField(max_length=20, choices=ROLES)
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name='role_permissions'
    )
    is_granted = models.BooleanField(default=False)

    class Meta:
        unique_together = ['role', 'permission']

    def __str__(self):
        return f"{self.role} | {self.permission.code} = {'YES' if self.is_granted else 'NO'}"


class UserPermissionOverride(models.Model):
    """
    Per-employee permission overrides.
    If a record exists here, it OVERRIDES the role-level default.
    Use this to give a specific employee extra (or fewer) permissions.
    """
    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='permission_overrides'
    )
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name='user_overrides'
    )
    is_granted = models.BooleanField(default=True)
    reason     = models.CharField(max_length=200, blank=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='granted_overrides'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'permission']
        ordering = ['user__username', 'permission__module']

    def __str__(self):
        return f"{self.user.username} | {self.permission.code} = {'GRANTED' if self.is_granted else 'REVOKED'}"
