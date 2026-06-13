# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
import re


PERMISSION_MODULE_ALIASES = {
    'users': ['USER'],
    'user': ['USER'],
    'permissions': ['PERMISSION', 'SETTINGS'],
    'permission': ['PERMISSION', 'SETTINGS'],
    'roles': ['ROLE', 'SETTINGS'],
    'role': ['ROLE', 'SETTINGS'],
    'employees': ['EMPLOYEE', 'USER'],
    'employee': ['EMPLOYEE', 'USER'],
    'departments': ['DEPARTMENT', 'EMPLOYEE'],
    'department': ['DEPARTMENT', 'EMPLOYEE'],
    'attendance': ['ATTENDANCE', 'HRMS'],
    'regularize': ['ATTENDANCE', 'HRMS'],
    'regularization': ['ATTENDANCE', 'HRMS'],
    'leave': ['LEAVE', 'HRMS'],
    'salary': ['PAYROLL', 'HRMS'],
    'payroll': ['PAYROLL', 'HRMS'],
    'payslip': ['PAYROLL', 'HRMS'],
    'reports': ['REPORT', 'REPORTS'],
    'report': ['REPORT', 'REPORTS'],
    'settings': ['SETTINGS', 'SETTINGS_MANAGE'],
    'support_tickets': ['SUPPORT_TICKET', 'SUPPORT'],
    'affiliate': ['AFFILIATE'],
    'leads': ['LEAD', 'CRM'],
    'lead': ['LEAD', 'CRM'],
    'lead_analytics': ['LEAD_ANALYTICS', 'LEAD', 'CRM'],
    'lead_forms': ['LEAD_FORM', 'LEAD_FORMS', 'LEAD', 'CRM'],
    'followups': ['LEAD', 'CRM'],
    'followup': ['LEAD', 'CRM'],
    'tasks': ['TASK'],
    'task': ['TASK'],
    'team_tasks': ['TASK'],
    'revenue': ['REVENUE'],
}

PERMISSION_ACTION_ALIASES = {
    'view': ['VIEW', 'READ'],
    'create': ['CREATE', 'ADD'],
    'edit': ['UPDATE', 'EDIT'],
    'delete': ['DELETE', 'REMOVE', 'DISABLE'],
    'configure': ['CONFIGURE', 'MANAGE', 'UPDATE'],
    'manage': ['MANAGE', 'UPDATE'],
    'approve': ['APPROVE', 'ACTION'],
    'process': ['PROCESS', 'CREATE'],
    'export': ['EXPORT', 'VIEW'],
    'apply': ['APPLY', 'CREATE'],
    'cancel': ['CANCEL', 'DELETE'],
    'assign': ['ASSIGN', 'UPDATE'],
    'raise': ['CREATE', 'RAISE'],
}


def _normalize_permission_code(value):
    return re.sub(r'[^a-z0-9]+', '_', str(value or '').lower()).strip('_')


def _permission_matches(granted_code, required_code):
    granted = _normalize_permission_code(granted_code)
    required = _normalize_permission_code(required_code)
    if granted in {'*', 'all', 'all_permissions'}:
        return True
    if granted == required:
        return True

    parts = required.split('_')
    if len(parts) >= 2:
        action = parts[0]
        module = '_'.join(parts[1:])
        aliases = {
            f'{module}_{action}',
            f'{action}_{module}',
            f'{module}_{required}',
            f'{required}_{module}',
        }
        return granted in aliases

    return False


def _java_permission_candidates(required_code):
    required = _normalize_permission_code(required_code)
    parts = required.split('_')
    candidates = {
        required.upper(),
        required.replace('_', '.').upper(),
        required.replace('_', ':').upper(),
    }

    if len(parts) >= 2:
        action = parts[0]
        module = '_'.join(parts[1:])
        modules = PERMISSION_MODULE_ALIASES.get(module, [module.upper()])
        actions = PERMISSION_ACTION_ALIASES.get(action, [action.upper()])
        for module_name in modules:
            for action_name in actions:
                candidates.add(f'{module_name}_{action_name}')
                candidates.add(f'{module_name}.{action_name}')
                candidates.add(f'{module_name}:{action_name}')
                candidates.add(f'HRMS_{module_name}_{action_name}')
                candidates.add(f'{module_name}_{required.upper()}')

    if required in {'configure_leave', 'approve_leave', 'apply_leave', 'view_leave', 'cancel_leave', 'view_all_leave'}:
        suffix = required.upper()
        candidates.update({
            suffix,
            f'HRMS_{suffix}',
            f'LEAVE_{parts[0].upper()}',
            f'HRMS_LEAVE_{parts[0].upper()}',
        })

    if required == 'manage_settings':
        candidates.update({
            'SETTINGS_MANAGE',
            'SETTINGS_MANAGE_ONBOARDING',
            'SETTINGS_MANAGE_TEMPLATES',
            'COMPANY_PROFILE_UPDATE',
            'ATTENDANCE_MANAGE',
            'ATTENDANCE_UPDATE',
            'HRMS_MANAGE_SETTINGS',
            'HRMS_ATTENDANCE_MANAGE',
        })

    if required in {'approve_regularize', 'approve_regularization', 'approve_attendance'}:
        candidates.update({
            'ATTENDANCE_APPROVE',
            'ATTENDANCE_ACTION',
            'ATTENDANCE_MANAGE',
            'HRMS_ATTENDANCE_APPROVE',
            'HRMS_ATTENDANCE_ACTION',
            'HRMS_ATTENDANCE_MANAGE',
            'APPROVE_ATTENDANCE',
            'APPROVE_REGULARIZATION',
            'REGULARIZATION_APPROVE',
        })

    return candidates


def _permission_public_aliases(code):
    normalized = _normalize_permission_code(code)
    if not normalized:
        return set()

    raw = str(code or '').strip()
    aliases = {
        raw,
        normalized,
        normalized.upper(),
        normalized.replace('_', '.').upper(),
        normalized.replace('_', ':').upper(),
    }

    aliases.update(_java_permission_candidates(normalized))

    parts = normalized.split('_')
    if len(parts) >= 2:
        action = parts[0]
        module = '_'.join(parts[1:])
        for module_name in PERMISSION_MODULE_ALIASES.get(module, [module.upper()]):
            for action_name in PERMISSION_ACTION_ALIASES.get(action, [action.upper()]):
                aliases.add(f'{module_name}_{action_name}')

    upper_raw = raw.upper()
    if upper_raw.endswith(':*') or upper_raw.endswith('.*'):
        aliases.add(f'{upper_raw[:-2]}_*')

    return {alias for alias in aliases if alias}


def _expand_permission_codes(codes):
    expanded = []
    seen = set()
    for code in codes or []:
        for alias in _permission_public_aliases(code):
            if alias not in seen:
                expanded.append(alias)
                seen.add(alias)
    return expanded


def _module_allows_permission(java_modules, required_code):
    modules = {_normalize_permission_code(module).upper() for module in (java_modules or [])}
    required = _normalize_permission_code(required_code)

    if not modules:
        return False

    module_groups = {
        'HRMS': {
            'attendance', 'leave', 'payroll', 'salary', 'payslip',
            'employees', 'employee', 'departments', 'department',
            'settings',
        },
        'ATTENDANCE': {'attendance', 'settings'},
        'PAYROLL': {'payroll', 'salary', 'payslip'},
        'EMPLOYEE': {'employees', 'employee', 'departments', 'department'},
        'LEAD': {'leads', 'lead', 'followups', 'followup'},
        'CRM': {'leads', 'lead', 'followups', 'followup'},
        'AFFILIATE': {'affiliate'},
        'TASK': {'tasks', 'task', 'team_tasks'},
        'REPORT': {'reports', 'report'},
        'REPORTS': {'reports', 'report'},
    }

    parts = required.split('_')
    if len(parts) < 2:
        return False
    permission_module = '_'.join(parts[1:])

    for java_module, allowed_modules in module_groups.items():
        if java_module in modules and permission_module in allowed_modules:
            return True
    return False


class Tenant(models.Model):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class CustomRole(models.Model):
    tenant_id = models.CharField(max_length=64, default='default', db_index=True)
    name        = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    level       = models.IntegerField(default=10)
    base_role   = models.CharField(max_length=20, default='employee')
    is_active   = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['level', 'name']

    def __str__(self):
        return f"{self.display_name} (level {self.level})"


class User(AbstractUser):
    BASE_ROLES = [
        ('superadmin', 'SuperAdmin'),
        ('admin',      'Admin'),
        ('manager',    'Manager'),
        ('hr',         'HR'),
        ('counselor',  'Counselor'),
        ('employee',   'Employee'),
    ]
    EMP_TYPES = [
        ('regular',  'Regular'),
        ('contract', 'Contract'),
        ('parttime', 'Part-Time'),
        ('intern',   'Intern'),
    ]

    role          = models.CharField(max_length=20, choices=BASE_ROLES, default='employee')
    tenant_id     = models.CharField(max_length=64, default='default', db_index=True)
    custom_role   = models.ForeignKey(
        CustomRole, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='users'
    )
    employee_type = models.CharField(max_length=20, choices=EMP_TYPES, default='regular')
    created_by    = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='created_users'
    )

    def __str__(self):
        label = self.custom_role.display_name if self.custom_role else self.role
        return f"{self.username} ({label})"

    def get_effective_role(self):
        if self.is_superuser:
            return 'superadmin'
        if self.custom_role and self.custom_role.is_active and self.custom_role.base_role:
            return self.custom_role.base_role
        return self.role

    def get_display_role(self):
        if self.custom_role:
            return self.custom_role.display_name
        return dict(self.BASE_ROLES).get(self.role, self.role)

    def get_permissions_list(self):
        """
        Django superuser: all permissions granted.
        Normal users: only explicitly granted user permissions.
        """
        java_permissions = getattr(self, '_java_permissions', None)
        if java_permissions is not None:
            if getattr(self, '_java_is_superuser', False) or '*' in java_permissions:
                from utils.models import Permission
                codes = list(Permission.objects.values_list('code', flat=True))
                if codes:
                    return _expand_permission_codes(codes)
                from utils.permission_registry import ALL_CODES
                return _expand_permission_codes(ALL_CODES)
            if java_permissions:
                return _expand_permission_codes(java_permissions)
            return []

        from utils.models import Permission, UserPermissionOverride

        if self.is_superuser:
            return _expand_permission_codes(Permission.objects.values_list('code', flat=True))

        return _expand_permission_codes(UserPermissionOverride.objects.filter(
            user=self,
            is_granted=True,
        ).values_list('permission__code', flat=True))

    def has_perm_code(self, code):
        java_permissions = getattr(self, '_java_permissions', None)
        if java_permissions is not None:
            if getattr(self, '_java_is_superuser', False):
                return True
            java_candidates = {_normalize_permission_code(candidate) for candidate in _java_permission_candidates(code)}
            if any(
                _permission_matches(permission, code) or
                _normalize_permission_code(permission) in java_candidates
                for permission in java_permissions
            ):
                return True
            java_token = getattr(self, '_java_token', None)
            if java_token:
                from utils.java_bridge import check_permission

                cache = getattr(self, '_java_permission_check_cache', None)
                if cache is None:
                    cache = {}
                    self._java_permission_check_cache = cache

                for candidate in _java_permission_candidates(code):
                    if candidate not in cache:
                        cache[candidate] = check_permission(java_token, candidate)
                    if cache[candidate]:
                        return True

            return False

        from utils.models import UserPermissionOverride

        if self.is_superuser:
            return True

        return UserPermissionOverride.objects.filter(
            user=self,
            permission__code=code,
            is_granted=True,
        ).exists()
