# leave/utils.py
"""
Leave utilities — all weekend/working-day logic reads from settings_helper.
Carry-forward logic lives here and is called by the management command.

ADDED:
  sync_balances_for_leave_type() — called whenever a LeaveType is created
  or its days_allowed is changed, so all existing employee LeaveBalance rows
  stay in sync without requiring manual admin action.

FIX: process_carry_forward() now respects the system-settings override for
     carry_forward (e.g. cl_carry_forward = false disables CL carry-forward
     even if LeaveType.carry_forward is True on the model).

FIX: get_leave_balance_summary() now returns the effective carry_forward
     flag (system settings win over model), so the frontend calendar
     estimation and BalanceDashboard correctly show/hide the CF section.
"""
from datetime import date, timedelta
from decimal import Decimal
from .models import LeaveBalance, LeaveType


def get_weekend_days_set() -> set:
    """Returns set of weekend day names from settings."""
    try:
        from attendance.settings_helper import get_weekend_days
        return set(get_weekend_days())
    except Exception:
        return {'saturday', 'sunday'}


def is_working_day(d: date) -> bool:
    """Returns True if d is NOT a weekend day per system settings."""
    DAY_NAMES = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
    return DAY_NAMES[d.weekday()] not in get_weekend_days_set()


def count_working_days(start_date: date, end_date: date, session: str = 'full') -> float:
    """
    Count working days between two dates using weekend_days setting.
    session='first_half' or 'second_half' always returns 0.5.
    """
    if session in ('first_half', 'second_half'):
        return 0.5

    count = 0
    cur = start_date
    while cur <= end_date:
        if is_working_day(cur):
            count += 1
        cur += timedelta(days=1)
    return count


def _effective_days_allowed(leave_type: LeaveType) -> int:
    return leave_type.days_allowed


def _is_earned_leave_type(leave_type: LeaveType) -> bool:
    code = (leave_type.code or '').upper()
    return code in ('EL', 'PL') or 'earned' in (leave_type.name or '').lower()


def _employee_joining_date(employee):
    profile = getattr(employee, 'profile', None)
    joining_date = getattr(profile, 'joining_date', None)
    if not joining_date:
        joining_date = getattr(employee, 'date_joined', None)
    if hasattr(joining_date, 'date'):
        joining_date = joining_date.date()
    return joining_date


def _is_employee_on_probation(employee, as_of: date = None) -> bool:
    if as_of is None:
        as_of = date.today()

    try:
        from attendance.settings_helper import get_probation_months
        from dateutil.relativedelta import relativedelta

        prob_months = int(get_probation_months())
        if prob_months <= 0:
            return False

        joining_date = _employee_joining_date(employee)
        if not joining_date:
            return False

        probation_end = joining_date + relativedelta(months=prob_months)
        return as_of < probation_end
    except Exception:
        return False


def _probation_earned_leave_allowed() -> bool:
    try:
        from attendance.settings_helper import _get, _parse_bool
        return _parse_bool(_get('probation_earned_leave', False))
    except Exception:
        return False


def _base_allocation_for_employee(employee, leave_type: LeaveType, as_of: date = None) -> int:
    days_allowed = _effective_days_allowed(leave_type)
    if (
        _is_earned_leave_type(leave_type)
        and _is_employee_on_probation(employee, as_of)
        and not _probation_earned_leave_allowed()
    ):
        return 0
    return days_allowed


def _sync_balance_total(balance: LeaveBalance, base_allocation) -> bool:
    carried = Decimal(str(balance.carried or 0))
    new_total = Decimal(str(base_allocation)) + carried
    min_total = Decimal(str(balance.used or 0)) + Decimal(str(balance.pending or 0))
    if new_total < min_total:
        new_total = min_total

    if balance.total == new_total:
        return False

    balance.total = new_total
    balance.save(update_fields=['total'])
    return True


def get_or_create_balance(employee, leave_type, year: int) -> LeaveBalance:
    base_allocation = _base_allocation_for_employee(employee, leave_type)
    balance, _ = LeaveBalance.objects.get_or_create(
        employee=employee,
        leave_type=leave_type,
        year=year,
        tenant_id=getattr(employee, 'tenant_id', 'default') or 'default',
        defaults={'total': base_allocation},
    )
    _sync_balance_total(balance, base_allocation)
    return balance


def init_balances_for_employee(employee, year: int = None) -> int:
    """
    Create LeaveBalance rows for all applicable leave types for this employee/year.
    Called on first login of a new year and when a new employee is created.
    Respects probation_period_months — EL total is set to 0 during probation.
    """
    if year is None:
        year = date.today().year

    # ── Probation check ──────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────

    emp_type = getattr(employee, 'employee_type', 'regular')
    types = LeaveType.objects.filter(
        is_active=True,
        tenant_id=getattr(employee, 'tenant_id', 'default') or 'default',
    ).filter(applicable_to__in=['all', emp_type])

    created_count = 0
    for lt in types:
        allocated = _base_allocation_for_employee(employee, lt)

        balance, created = LeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type=lt,
            year=year,
            tenant_id=getattr(employee, 'tenant_id', 'default') or 'default',
            defaults={'total': allocated},
        )
        if created:
            created_count += 1
        else:
            _sync_balance_total(balance, allocated)

    return created_count


def sync_balances_for_leave_type(leave_type: LeaveType, year: int = None) -> dict:
    """
    Called whenever a LeaveType is created or days_allowed is changed.

    For each active employee:
      - If no LeaveBalance exists for this year → CREATE one with total=days_allowed
      - If a balance exists AND the base total (total - carried) differs from
        days_allowed → UPDATE total to keep base allocation in sync.
        (Does NOT reduce total below already-used days.)

    Returns a summary dict:  {created: N, updated: N, skipped: N}
    """
    if year is None:
        year = date.today().year

    from accounts.models import User
    emp_type = leave_type.applicable_to

    if emp_type == 'all':
        employees = User.objects.filter(is_active=True, tenant_id=leave_type.tenant_id)
    else:
        employees = User.objects.filter(is_active=True, employee_type=emp_type, tenant_id=leave_type.tenant_id)

    created = updated = skipped = 0

    for emp in employees:
        base_allocation = _base_allocation_for_employee(emp, leave_type)
        bal, was_created = LeaveBalance.objects.get_or_create(
            employee=emp,
            leave_type=leave_type,
            year=year,
            tenant_id=leave_type.tenant_id,
            defaults={
                'total':   base_allocation,
                'used':    0,
                'pending': 0,
                'carried': 0,
            },
        )
        if was_created:
            created += 1
        else:
            # Compute what the base allocation should be (total minus any carried days)
            carried = float(bal.carried or 0)
            old_base = float(bal.total) - carried
            new_base = float(base_allocation)

            if abs(old_base - new_base) < 0.01:
                skipped += 1
                continue

            # Update total = new base + carried (preserve carry-forward days)
            bal.total = new_base + carried
            # Safety: total must not drop below used + pending
            min_total = float(bal.used) + float(bal.pending)
            if float(bal.total) < min_total:
                bal.total = min_total
            bal.save(update_fields=['total'])
            updated += 1

    return {'created': created, 'updated': updated, 'skipped': skipped, 'year': year}


def _effective_carry_forward(lt: LeaveType) -> bool:
    """
    Fully dynamic carry-forward from LeaveTypeConfig only.
    No System Settings dependency.
    """
    return bool(
        lt.carry_forward
    )

def process_carry_forward(year: int = None) -> dict:
    """
    Year-end carry-forward engine.
    Called for year Y:
      - For each employee, for each leave type with carry_forward=True
        (respecting system-settings override via _effective_carry_forward):
          carried = min(prev_year.remaining, lt.max_carry_forward)
      - Creates/updates next-year balance row with carried amount added to total.
      - Marks prev_year balance as processed (carried field updated).

    FIX: carry_forward is now evaluated via _effective_carry_forward() so
         a system-settings override of cl_carry_forward=false actually
         disables CL carry-forward even if the LeaveType model flag is True.

    Returns summary dict with counts.
    """


    if year is None:
        year = date.today().year  # year = the year ENDING (carry FROM this year TO next)

    next_year = year + 1
    processed = 0
    skipped   = 0

    # Start with ALL active leave types — filter by effective carry_forward below
    all_leave_types = LeaveType.objects.filter(is_active=True)

    # Only process types where carry_forward is effectively True
    carry_types = [lt for lt in all_leave_types if _effective_carry_forward(lt)]

    for lt in carry_types:
        # Global cap from settings for EL; use lt.max_carry_forward for others
        # Fully dynamic carry forward from LeaveTypeConfig only

        effective_cap = float(
    lt.max_carry_forward or 0
)
        prev_balances = LeaveBalance.objects.filter(leave_type=lt, year=year)

        for prev_bal in prev_balances:
            emp = prev_bal.employee

            remaining  = float(prev_bal.remaining)
            carry_days = min(remaining, effective_cap)

            if carry_days <= 0:
                skipped += 1
                continue

            prev_bal.carried = carry_days
            prev_bal.save(update_fields=['carried'])

            next_bal, created = LeaveBalance.objects.get_or_create(
                employee=emp,
                leave_type=lt,
                year=next_year,
                tenant_id=getattr(emp, 'tenant_id', 'default') or 'default',
                defaults={'total': _base_allocation_for_employee(emp, lt)},
            )

            # base allocation + carry-forward
            next_bal.total   = _base_allocation_for_employee(emp, lt) + carry_days
            next_bal.carried = carry_days
            next_bal.save(update_fields=['total', 'carried'])

            processed += 1

    return {
        'year_from': year,
        'year_to':   next_year,
        'processed': processed,
        'skipped':   skipped,
    }


def get_leave_balance_summary(employee, year: int) -> list:
    """
    Returns balance rows for employee/year including carry-forward details.

    FIX: carry_forward is now the effective value (system settings win over
         model), so the frontend calendar estimation and BalanceDashboard
         carry-forward section correctly appear/disappear based on the
         system setting (e.g. cl_carry_forward=false hides CL from CF display).
    """
    balances = LeaveBalance.objects.filter(
        employee=employee,
        year=year,
        tenant_id=getattr(employee, 'tenant_id', 'default') or 'default',
    ).select_related('leave_type').order_by('leave_type__name')

    result = []
    for bal in balances:
        carried   = float(bal.carried or 0)
        base      = float(_base_allocation_for_employee(employee, bal.leave_type))
        if _sync_balance_total(bal, base):
            bal.refresh_from_db(fields=['total'])
        total     = float(bal.total)
        used      = float(bal.used)
        pending   = float(bal.pending)
        remaining = max(total - used - pending, 0)

        this_year_remaining = max(min(remaining, base), 0)
        cf_remaining        = max(remaining - this_year_remaining, 0)

        # FIX: use effective carry_forward (system settings override > model)
        eff_carry_forward = _effective_carry_forward(bal.leave_type)

        result.append({
            'id':              bal.id,
            'leave_type_id':   bal.leave_type.id,
            'leave_type_name': bal.leave_type.name,
            'leave_type_code': bal.leave_type.code,
            'is_paid':         bal.leave_type.is_paid,
            'carry_forward':   eff_carry_forward,   # FIX: effective value, not raw model
            'max_carry_forward': bal.leave_type.max_carry_forward,
            'year':            year,
            'base_allocation': base,
            'carried_forward': carried,
            'total':           total,
            'used':            used,
            'pending':         pending,
            'remaining':       remaining,
            'this_year_remaining': this_year_remaining,
            'cf_remaining':    cf_remaining,
        })

    return result
