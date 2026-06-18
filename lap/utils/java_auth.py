from __future__ import annotations

import re
from typing import Optional

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from utils.java_bridge import current_user, validate_token


DEV_FALLBACK_MODULES = {
    'HRMS',
    'ATTENDANCE',
    'LEAVE',
    'PAYROLL',
    'EMPLOYEE',
    'TASK',
    'AFFILIATE',
    'CRM',
    'LEAD',
    'REPORT',
    'REPORTS',
    'SETTINGS',
}


def _split_values(raw_value: Optional[str]) -> set[str]:
    if not raw_value:
        return set()
    return {value.strip() for value in raw_value.split(',') if value.strip()}


def _claim_values(claims: dict, *keys: str) -> set[str]:
    values: set[str] = set()
    for key in keys:
        raw_value = claims.get(key)
        if raw_value is None:
            continue
        if isinstance(raw_value, str):
            values.update(_split_values(raw_value))
        elif isinstance(raw_value, (list, tuple, set)):
            values.update(str(value).strip() for value in raw_value if str(value).strip())
    return values


def _first_value(*values):
    for value in values:
        if value not in (None, ''):
            return value
    return None


def _normalize_role(value: Optional[str]) -> str:
    return re.sub(r'[^a-z0-9]+', '_', value or '', flags=re.IGNORECASE).strip('_').lower()


def _base_role(value: Optional[str]) -> str:
    role = _normalize_role(value)
    if role in {'super_admin', 'superadmin', 'platform_admin', 'system_admin'}:
        return 'superadmin'
    if role in {'tenant_admin', 'company_admin', 'admin'}:
        return 'admin'
    if role in {'human_resources', 'hr_manager', 'hr'}:
        return 'hr'
    if role in {'team_manager', 'manager'}:
        return 'manager'
    if role in {'counsellor', 'counselor'}:
        return 'counselor'
    if 'super' in role and 'admin' in role:
        return 'superadmin'
    if 'admin' in role:
        return 'admin'
    if role.startswith('hr') or '_hr' in role or 'human_resource' in role:
        return 'hr'
    if 'manager' in role:
        return 'manager'
    if 'counsel' in role:
        return 'counselor'
    return 'employee'


def _is_external_admin(role: Optional[str], claims: dict) -> bool:
    if claims.get('isPlatformAdmin') is True or claims.get('platformAdmin') is True:
        return True
    tenant_code = str(
        _first_value(
            claims.get('tenantCode'),
            claims.get('tenant_code'),
            claims.get('tenantId'),
            claims.get('tenant_id'),
        ) or ''
    ).strip().upper()
    if tenant_code == 'SYS':
        return True
    return _normalize_role(role) in {
        'super_admin',
        'superadmin',
        'platform_admin',
        'system_admin',
        'tenant_admin',
        'company_admin',
        'admin',
    } or 'admin' in _normalize_role(role)


def _extract_token(request) -> Optional[str]:
    header = get_authorization_header(request).split()
    if header:
        if header[0].lower() == b'bearer' and len(header) == 2:
            return header[1].decode('utf-8')
        if len(header) == 2 and header[0].lower() in {b'token', b'jwt'}:
            return header[1].decode('utf-8')
        if len(header) == 1:
            return header[0].decode('utf-8')
        if len(header) == 2:
            return header[1].decode('utf-8')
        return None

    for header_name in ('X-Authorization', 'X-Auth-Token', 'X-Access-Token', 'X-Java-Token'):
        value = request.headers.get(header_name)
        if value:
            return value.removeprefix('Bearer ').strip()

    for cookie_name in ('token', 'auth_token', 'access_token', 'accessToken'):
        value = request.COOKIES.get(cookie_name)
        if value:
            return value

    query_token = request.query_params.get('token') if hasattr(request, 'query_params') else None
    return query_token or None


class JavaTokenAuthentication(BaseAuthentication):
    """Authenticate requests using the JWT issued by the Java auth backend."""

    def authenticate(self, request):
        token = _extract_token(request)
        if not token:
            fallback = self._authenticate_from_trusted_tenant_headers(request)
            return fallback

        try:
            claims = self._decode_token(token)
        except AuthenticationFailed:
            fallback = self._authenticate_from_trusted_tenant_headers(request)
            if fallback:
                return fallback
            raise
        java_profile = validate_token(token)
        java_current_user = current_user(token)
        if java_current_user:
            java_profile = {**java_profile, **java_current_user}
        user = self._get_or_create_user(claims, request, java_profile)

        java_permissions = (
            _claim_values(claims, 'permissions', 'permissionCodes', 'authorities', 'scope', 'scopes') |
            _claim_values(java_current_user, 'permissions', 'permissionCodes', 'authorities') |
            _split_values(request.headers.get('X-Java-Permissions'))
        )
        java_modules = (
            _claim_values(claims, 'modules', 'moduleCodes', 'enabledModules') |
            _claim_values(java_current_user, 'modules', 'moduleCodes', 'enabledModules') |
            _split_values(request.headers.get('X-Java-Modules'))
        )
        java_role = _first_value(
            request.headers.get('X-Java-Role'),
            java_profile.get('role'),
            java_profile.get('roleName'),
            claims.get('roleName'),
            claims.get('role'),
            claims.get('authority'),
        )
        java_user_id = _first_value(
            request.headers.get('X-Java-User-Id'),
            java_profile.get('userId'),
            claims.get('userId'),
            claims.get('id'),
            claims.get('sub'),
        )
        java_tenant_id = _resolve_tenant_id(claims, request, java_profile)

        user._java_token = token
        user._java_claims = claims
        user._java_profile = java_profile
        user._java_permissions = java_permissions
        user._java_modules = java_modules
        user._java_role = java_role
        user._java_base_role = _base_role(java_role)
        user._java_user_id = str(java_user_id) if java_user_id is not None else None
        user._java_tenant_id = java_tenant_id
        user._java_is_superuser = _is_external_admin(java_role, claims) or '*' in java_permissions

        return user, token

    def _authenticate_from_trusted_tenant_headers(self, request):
        if not getattr(settings, 'LAP_TRUST_TENANT_HEADER_AUTH', False):
            return None

        tenant_id = _first_value(
            request.headers.get('X-Tenant'),
            request.headers.get('X-Tenant-Code'),
        )
        if not tenant_id:
            return None

        email = _first_value(
            request.headers.get('X-User-Email'),
            request.headers.get('X-Java-User-Email'),
            request.headers.get('X-Java-User-Id'),
            f'java-user-{tenant_id}@lap.local',
        )
        role_value = _first_value(
            request.headers.get('X-Java-Role'),
            request.headers.get('X-Role'),
            'ADMIN',
        )
        claims = {
            'sub': str(email),
            'tenantId': str(tenant_id),
            'tenantCode': str(tenant_id),
            'role': role_value,
        }
        user = self._get_or_create_user(claims, request, {'role': role_value})

        java_permissions = _split_values(request.headers.get('X-Java-Permissions'))
        java_modules = _split_values(request.headers.get('X-Java-Modules')) or set(DEV_FALLBACK_MODULES)

        user._java_token = None
        user._java_claims = claims
        user._java_profile = {'role': role_value}
        user._java_permissions = java_permissions
        user._java_modules = java_modules
        user._java_role = role_value
        user._java_base_role = _base_role(role_value)
        user._java_user_id = str(email)
        user._java_tenant_id = str(tenant_id)
        user._java_is_superuser = _is_external_admin(role_value, claims) or '*' in java_permissions

        return user, None

    def _decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(
                token,
                settings.JAVA_JWT_SECRET,
                algorithms=['HS256'],
                options={'verify_aud': False},
            )
        except jwt.ExpiredSignatureError as exc:
            if getattr(settings, 'LAP_ALLOW_UNVERIFIED_JAVA_JWT', False):
                return self._decode_unverified_token(token)
            raise AuthenticationFailed('Token has expired') from exc
        except jwt.PyJWTError as exc:
            if getattr(settings, 'LAP_ALLOW_UNVERIFIED_JAVA_JWT', False):
                return self._decode_unverified_token(token)
            raise AuthenticationFailed('Invalid token') from exc

    def _decode_unverified_token(self, token: str) -> dict:
        try:
            claims = jwt.decode(
                token,
                options={
                    'verify_signature': False,
                    'verify_exp': False,
                    'verify_aud': False,
                },
                algorithms=['HS256'],
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationFailed('Invalid token') from exc
        if not isinstance(claims, dict):
            raise AuthenticationFailed('Invalid token')
        return claims

    def _get_or_create_user(self, claims: dict, request, java_profile: dict | None = None):
        java_profile = java_profile or {}
        email = claims.get('sub') or claims.get('email')
        if not email:
            raise AuthenticationFailed('Token is missing the user email')

        tenant_id = _resolve_tenant_id(claims, request, java_profile)
        role_value = _first_value(
            request.headers.get('X-Java-Role'),
            java_profile.get('role'),
            java_profile.get('roleName'),
            claims.get('roleName'),
            claims.get('role'),
            claims.get('authority'),
        )
        base_role = _base_role(role_value)
        username = email

        user_model = get_user_model()
        user = user_model.objects.filter(email=email).first()
        if user is None:
            user = user_model(
                username=username,
                email=email,
                tenant_id=str(tenant_id) if tenant_id is not None else 'default',
                role=base_role,
                is_active=True,
            )
            user.set_unusable_password()
            user.save()
            try:
                _sync_user_profile_and_manager(user, claims, java_profile, request)
            except Exception:
                pass
            return user

        updates = []
        if user.username != username:
            user.username = username
            updates.append('username')
        tenant_value = str(tenant_id) if tenant_id is not None else 'default'
        if getattr(user, 'tenant_id', None) != tenant_value:
            user.tenant_id = tenant_value
            updates.append('tenant_id')
        if getattr(user, 'role', None) != base_role:
            user.role = base_role
            updates.append('role')
        if not user.is_active:
            user.is_active = True
            updates.append('is_active')
        if updates:
            user.save(update_fields=updates)
        try:
            _sync_user_profile_and_manager(user, claims, java_profile, request)
        except Exception:
            pass
        return user


def _sync_user_profile_and_manager(user, claims: dict, java_profile: dict | None, request):
    from datetime import date
    from employees.models import EmployeeProfile
    from accounts.models import User as AccountUser

    java_profile = java_profile or {}
    claims = claims or {}

    # 1. Gather all profile fields
    # Resolve emp_code
    emp_code = (
        claims.get('emp_code') or claims.get('employeeId') or claims.get('empCode') or claims.get('employeeCode') or
        java_profile.get('emp_code') or java_profile.get('employeeId') or java_profile.get('empCode') or java_profile.get('employeeCode') or
        request.headers.get('X-Java-Employee-Id') or
        f"EMP-{user.id}"
    )
    emp_code = str(emp_code).strip()[:20]

    # Resolve designation
    designation_raw = (
        claims.get('designation') or java_profile.get('designation') or
        request.headers.get('X-Java-Designation')
    )

    # Resolve work_mode
    work_mode_raw = (
        claims.get('work_mode') or claims.get('workMode') or
        java_profile.get('work_mode') or java_profile.get('workMode') or
        request.headers.get('X-Java-Work-Mode')
    )

    # Resolve joining_date
    joining_date_raw = (
        claims.get('joining_date') or claims.get('joiningDate') or
        java_profile.get('joining_date') or java_profile.get('joiningDate') or
        request.headers.get('X-Java-Joining-Date')
    )

    # Map raw fields to choices
    allowed_designations = {
        'software_engineer', 'senior_engineer', 'team_lead', 'project_manager',
        'hr_executive', 'hr_manager', 'accountant', 'analyst', 'intern', 'other'
    }
    designation = 'other'
    if designation_raw:
        norm_desig = str(designation_raw).lower().replace('-', '_').replace(' ', '_')
        if norm_desig in allowed_designations:
            designation = norm_desig

    work_mode = 'office'
    if work_mode_raw:
        norm_wm = str(work_mode_raw).lower().replace('-', '_').replace(' ', '_')
        if norm_wm in {'office', 'work_from_home'}:
            work_mode = norm_wm

    joining_date = date.today()
    if joining_date_raw:
        try:
            if isinstance(joining_date_raw, str):
                joining_date = date.fromisoformat(joining_date_raw.split('T')[0])
        except Exception:
            pass

    # Get or create EmployeeProfile
    profile, created = EmployeeProfile.objects.get_or_create(
        user=user,
        defaults={
            'tenant_id': user.tenant_id,
            'emp_code': emp_code,
            'designation': designation,
            'work_mode': work_mode,
            'joining_date': joining_date,
        }
    )

    profile_updates = []
    if profile.tenant_id != user.tenant_id:
        profile.tenant_id = user.tenant_id
        profile_updates.append('tenant_id')
    if emp_code and profile.emp_code != emp_code:
        if not EmployeeProfile.objects.filter(tenant_id=user.tenant_id, emp_code=emp_code).exclude(pk=profile.pk).exists():
            profile.emp_code = emp_code
            profile_updates.append('emp_code')

    # 2. Try to find the manager/supervisor user in Django
    manager_candidates = []

    for source in (claims, java_profile):
        for key in ('supervisor', 'manager', 'reportingTo'):
            val = source.get(key)
            if isinstance(val, dict):
                for subkey in ('email', 'username', 'id', 'userId', 'user_id'):
                    if val.get(subkey):
                        manager_candidates.append(str(val.get(subkey)).strip())
            elif val:
                manager_candidates.append(str(val).strip())

    for source in (claims, java_profile):
        for key in (
            'supervisorEmail', 'managerEmail', 'reportingToEmail', 'supervisor_email', 'manager_email',
            'supervisorUsername', 'managerUsername', 'reportingToUsername', 'supervisor_username', 'manager_username',
            'supervisorUserId', 'supervisor_id', 'managerId', 'manager_id', 'reportingToUserId',
        ):
            val = source.get(key)
            if val:
                manager_candidates.append(str(val).strip())

    for header in ('X-Java-Supervisor-Id', 'X-Java-Supervisor-Email', 'X-Java-Supervisor-Username'):
        val = request.headers.get(header)
        if val:
            manager_candidates.append(str(val).strip())

    manager_user = None
    for cand in manager_candidates:
        if not cand:
            continue
        if '@' in cand:
            mgr = AccountUser.objects.filter(email__iexact=cand, is_active=True).first()
            if mgr:
                manager_user = mgr
                break
        mgr = AccountUser.objects.filter(username__iexact=cand, is_active=True).first()
        if mgr:
            manager_user = mgr
            break
        if cand.isdigit():
            mgr = AccountUser.objects.filter(id=int(cand), is_active=True).first()
            if mgr:
                manager_user = mgr
                break
        java_email = f'java-user-{cand}@lap.local'
        mgr = AccountUser.objects.filter(email__iexact=java_email, is_active=True).first()
        if mgr:
            manager_user = mgr
            break
        mgr_profile = EmployeeProfile.objects.filter(tenant_id=user.tenant_id, emp_code__iexact=cand).first()
        if mgr_profile:
            manager_user = mgr_profile.user
            break

    if manager_user and manager_user.id != user.id:
        if profile.manager_id != manager_user.id:
            profile.manager = manager_user
            profile_updates.append('manager')

    if profile_updates:
        profile.save(update_fields=profile_updates)



def _resolve_tenant_id(claims: dict, request, java_profile: dict | None = None) -> str:
    java_profile = java_profile or {}
    tenant_value = _first_value(
        request.headers.get('X-Tenant'),
        request.headers.get('X-Tenant-Code'),
        java_profile.get('tenantId'),
        java_profile.get('tenantCode'),
        claims.get('tenantId'),
        claims.get('tenant_id'),
        claims.get('tenantCode'),
        claims.get('tenant_code'),
        claims.get('companyId'),
        claims.get('company_id'),
    )
    return str(tenant_value).strip()[:64] if tenant_value not in (None, '') else 'default'
