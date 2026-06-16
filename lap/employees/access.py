from datetime import date

from django.db.models import Q

from accounts.models import User
from accounts.tenant_utils import get_tenant_id


ADMIN_ROLES = {'superadmin'}
HR_ROLES = {'hr'}
MANAGER_ROLES = {'admin', 'hr', 'manager'}
TEAM_LEAD_DESIGNATIONS = {'team_lead', 'project_manager', 'hr_manager'}
BASE_ROLE_LEVELS = {
    'superadmin': 0,
    'admin': 10,
    'hr': 20,
    'manager': 30,
    'counselor': 40,
    'employee': 50,
}


def normalized_role(user):
    try:
        role = user.get_effective_role()
    except Exception:
        role = getattr(user, 'role', '')
    return str(role or '').lower().replace('-', '_')


def is_hrms_admin(user):
    return bool(getattr(user, 'is_superuser', False)) or normalized_role(user) in ADMIN_ROLES


def is_hr_user(user):
    return normalized_role(user) in HR_ROLES


def is_manager_like(user):
    if normalized_role(user) in MANAGER_ROLES:
        return True
    try:
        return user.profile.designation in TEAM_LEAD_DESIGNATIONS
    except Exception:
        return False


def role_level(user):
    custom_role = getattr(user, 'custom_role', None)
    if custom_role and getattr(custom_role, 'is_active', False):
        try:
            return int(custom_role.level)
        except (TypeError, ValueError):
            pass
    return BASE_ROLE_LEVELS.get(normalized_role(user), 100)


def role_group(user_or_role):
    if isinstance(user_or_role, str):
        role = user_or_role.lower().replace('-', '_')
    else:
        role = normalized_role(user_or_role)
        display = ''
        try:
            display = user_or_role.get_display_role()
        except Exception:
            display = getattr(user_or_role, 'role', '')
        role = f'{role} {display}'.lower().replace('-', '_')

    if 'super' in role or 'admin' in role:
        return 'admin'
    if 'hr' in role or 'human' in role:
        return 'hr'
    if 'manager' in role or 'head' in role or 'director' in role:
        return 'manager'
    if 'leader' in role or 'lead' in role or role in {'tl', 'teamleader'}:
        return 'team_lead'
    return 'employee'


def hierarchy_visibility_q(user):
    level = role_level(user)
    return (
        Q(custom_role__is_active=True, custom_role__level__gt=level) |
        Q(custom_role__isnull=True, role__in=[
            role for role, role_order in BASE_ROLE_LEVELS.items() if role_order > level
        ])
    )


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
    ) or '').strip()


def _java_role(item):
    return _java_value(item, 'roleName', 'role', 'authority') or 'employee'


def _java_base_role(value):
    role = str(value or '').lower().replace('-', '_').replace(' ', '_')
    if 'super' in role and 'admin' in role:
        return 'superadmin'
    if 'admin' in role:
        return 'admin'
    if 'hr' in role or 'human_resource' in role:
        return 'hr'
    if 'manager' in role or 'head' in role or 'director' in role:
        return 'manager'
    if 'counsel' in role:
        return 'counselor'
    return 'employee'


def _java_profile_data(item):
    profile = item.get('profileData') if isinstance(item, dict) else None
    return profile if isinstance(profile, dict) else {}


def _safe_designation(value):
    allowed = {
        'software_engineer',
        'senior_engineer',
        'team_lead',
        'project_manager',
        'hr_executive',
        'hr_manager',
        'accountant',
        'analyst',
        'intern',
        'other',
    }
    designation = str(value or 'other').lower().replace('-', '_').replace(' ', '_')
    return designation if designation in allowed else 'other'


def _safe_work_mode(value):
    work_mode = str(value or 'office').lower().replace('-', '_').replace(' ', '_')
    return work_mode if work_mode in {'office', 'work_from_home'} else 'office'


def _sync_java_reporting_users(request):
    token = getattr(request.user, '_java_token', None)
    current_java_id = str(getattr(request.user, '_java_user_id', '') or '').strip()
    if not token or not current_java_id:
        return

    cache_key = '_hrms_java_reporting_synced'
    if getattr(request, cache_key, False):
        return
    setattr(request, cache_key, True)

    try:
        from utils.java_bridge import list_users
        from employees.models import EmployeeProfile
    except Exception:
        return

    try:
        java_users = [item for item in list_users(token) if isinstance(item, dict) and item.get('active', True) is not False]
    except Exception:
        return

    if not java_users:
        return

    tenant_id = get_tenant_id(request)
    users_by_java_id = {}
    users_by_email = {}

    def sync_user(item):
        java_id = _java_user_id(item)
        if not java_id:
            return None

        profile_data = _java_profile_data(item)
        email = str(_java_value(item, 'email', 'username') or f'java-user-{java_id}@lap.local').strip()
        first_name = str(_java_value(item, 'firstName', 'first_name') or '').strip()
        last_name = str(_java_value(item, 'lastName', 'last_name') or '').strip()
        role = _java_base_role(_java_role(item))

        user = users_by_email.get(email.lower()) or User.objects.filter(email=email).first()
        created = False
        if user is None:
            username = email
            suffix = 1
            while User.objects.filter(username=username).exists():
                suffix += 1
                username = f'{email}-{suffix}'
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                tenant_id=tenant_id,
                role=role,
                is_active=True,
            )
            user.set_unusable_password()
            user.save()
            created = True

        updates = []
        for field, value in (
            ('tenant_id', tenant_id),
            ('role', role),
            ('first_name', first_name),
            ('last_name', last_name),
        ):
            if value and getattr(user, field) != value:
                setattr(user, field, value)
                updates.append(field)
        if not user.is_active:
            user.is_active = True
            updates.append('is_active')
        if updates and not created:
            user.save(update_fields=updates)

        emp_code = str(_java_value(
            item,
            'employeeId',
            'emp_code',
        ) or profile_data.get('emp_code') or profile_data.get('employeeId') or f'JAVA-{java_id}').strip()

        profile, profile_created = EmployeeProfile.objects.get_or_create(
            user=user,
            defaults={
                'tenant_id': tenant_id,
                'emp_code': emp_code[:20],
                'designation': _safe_designation(profile_data.get('designation')),
                'work_mode': _safe_work_mode(profile_data.get('work_mode') or profile_data.get('workMode')),
                'joining_date': profile_data.get('joining_date') or profile_data.get('joiningDate') or date.today(),
            },
        )
        profile_updates = []
        if profile.tenant_id != tenant_id:
            profile.tenant_id = tenant_id
            profile_updates.append('tenant_id')
        if emp_code and profile.emp_code != emp_code[:20]:
            unique_code = emp_code[:20]
            if EmployeeProfile.objects.filter(tenant_id=tenant_id, emp_code=unique_code).exclude(pk=profile.pk).exists():
                unique_code = f'JAVA-{java_id}'[:20]
            profile.emp_code = unique_code
            profile_updates.append('emp_code')
        if profile_updates and not profile_created:
            profile.save(update_fields=profile_updates)

        users_by_java_id[java_id] = user
        users_by_email[email.lower()] = user
        return user

    for item in java_users:
        sync_user(item)

    for item in java_users:
        java_id = _java_user_id(item)
        supervisor_id = _java_supervisor_id(item)
        user = users_by_java_id.get(java_id)
        manager = users_by_java_id.get(supervisor_id)
        if not user or not manager or user.id == manager.id:
            continue
        try:
            profile = user.profile
            if profile.manager_id != manager.id:
                profile.manager = manager
                profile.save(update_fields=['manager'])
        except Exception:
            pass


def visible_user_queryset(request, include_self=True):
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

    if is_manager_like(user):
        seen = set()
        frontier = [user.id]
        while frontier:
            children = list(qs.filter(profile__manager_id__in=frontier).values_list('id', flat=True))
            children += list(qs.filter(created_by_id__in=frontier).values_list('id', flat=True))
            next_frontier = [child for child in children if child not in seen and child != user.id]
            seen.update(next_frontier)
            frontier = next_frontier
        if include_self:
            seen.add(user.id)
        return qs.filter(id__in=seen).order_by('first_name', 'last_name', 'username')

    if include_self:
        return qs.filter(id=user.id)
    return qs.none()


def visible_user_ids(request, include_self=True):
    return list(visible_user_queryset(request, include_self).values_list('id', flat=True))


def user_is_visible(request, user_id, include_self=True):
    return visible_user_queryset(request, include_self).filter(id=user_id).exists()


def employee_profile_visibility_q(request):
    return Q(user_id__in=visible_user_ids(request))
