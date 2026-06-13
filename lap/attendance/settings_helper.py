# attendance/settings_helper.py
"""
Single source of truth for ALL system policy reads.
Every module imports from here — nothing hardcoded anywhere.
Adding a new setting = add a getter here.
"""
from datetime import time
from decimal import Decimal


def _get(key, default, tenant_id=None):
    try:
        from notifications.models import SystemSetting
        if tenant_id:
            s = (
                SystemSetting.objects.filter(tenant_id=str(tenant_id), key=key).first()
                or SystemSetting.objects.filter(tenant_id='default', key=key).first()
            )
        else:
            s = SystemSetting.objects.filter(key=key).first()
        if s:
            return s.get_value()
    except Exception:
        pass
    return default


def _parse_bool(val) -> bool:
    if isinstance(val, bool):
        return val
    if str(val).lower() in ('false', '0', 'no', 'off'):
        return False
    return bool(val)


# ── ATTENDANCE ────────────────────────────────────────────────────────────────

def _parse_time_setting(raw, fallback: time) -> time:
    try:
        parts = str(raw).strip().split(':')
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
        s = int(float(parts[2])) if len(parts) > 2 else 0
        return time(h, m, s)
    except Exception:
        return fallback


def get_shift_start(tenant_id=None) -> time:
    return _parse_time_setting(_get('work_start_time', '09:00', tenant_id), time(9, 0))


def get_shift_end(tenant_id=None) -> time:
    return _parse_time_setting(_get('work_end_time', '18:00', tenant_id), time(18, 0))


def get_night_shift_enabled(tenant_id=None) -> bool:
    return _parse_bool(_get('night_shift_enabled', False, tenant_id))


def get_night_shift_start(tenant_id=None) -> time:
    return _parse_time_setting(_get('night_shift_start_time', '22:00', tenant_id), time(22, 0))


def get_night_shift_end(tenant_id=None) -> time:
    return _parse_time_setting(_get('night_shift_end_time', '06:00', tenant_id), time(6, 0))


def is_time_in_shift(clock: time, start: time, end: time) -> bool:
    if start <= end:
        return start <= clock < end
    return clock >= start or clock < end


def get_active_shift_for_time(clock: time, tenant_id=None) -> dict:
    night_start = get_night_shift_start(tenant_id)
    night_end = get_night_shift_end(tenant_id)
    if get_night_shift_enabled(tenant_id) and is_time_in_shift(clock, night_start, night_end):
        return {
            'type': 'night',
            'start': night_start,
            'end': night_end,
            'is_overnight': night_end <= night_start,
        }
    day_start = get_shift_start(tenant_id)
    day_end = get_shift_end(tenant_id)
    return {
        'type': 'day',
        'start': day_start,
        'end': day_end,
        'is_overnight': day_end <= day_start,
    }


def get_grace_minutes(tenant_id=None) -> int:
    return int(_get('grace_period_minutes', 15, tenant_id))


def get_standard_hours(tenant_id=None) -> float:
    return float(_get('work_hours_per_day', 8, tenant_id))


def get_half_day_hours(tenant_id=None) -> float:
    return float(_get('half_day_hours', 4, tenant_id))


def get_late_per_half_day() -> int:
    return max(int(_get('late_marks_per_half_day', 3)), 1)


def get_overtime_multiplier() -> Decimal:
    return Decimal(str(_get('overtime_multiplier', 1.5)))


def get_regularization_window() -> int:
    return int(_get('regularization_window_days', 7))


def get_wfh_enabled() -> bool:
    return _parse_bool(_get('wfh_enabled', True))


def get_auto_absent_enabled() -> bool:
    return _parse_bool(_get('auto_absent_enabled', True))


def get_weekend_days() -> list:
    raw = _get('weekend_days', ['saturday', 'sunday'])
    if isinstance(raw, list):
        return [d.lower() for d in raw]
    try:
        import json
        parsed = json.loads(raw)
        return [d.lower() for d in parsed]
    except Exception:
        return ['saturday', 'sunday']


def get_work_days_per_week() -> int:
    return int(_get('work_days_per_week', 5))


def is_weekend(date_obj) -> bool:
    DAY_NAMES = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    day_name = DAY_NAMES[date_obj.weekday()]
    return day_name in get_weekend_days()


def get_working_days_in_month(year: int, month: int) -> tuple:
    import calendar
    from datetime import date
    from attendance.models import Holiday
    _, days_in_month = calendar.monthrange(year, month)
    holiday_dates = set(
        Holiday.objects.filter(date__year=year, date__month=month)
        .values_list('date', flat=True)
    )
    working = sum(
        1 for d in range(1, days_in_month + 1)
        if not is_weekend(date(year, month, d))
        and date(year, month, d) not in holiday_dates
    )
    return working, days_in_month

# ── PAYROLL — ALL 11 SETTINGS ─────────────────────────────────────────────────

def get_basic_salary_percent() -> Decimal:
    """Basic = Annual CTC × this% ÷ 12. Default 40."""
    return Decimal(str(_get('basic_salary_percent', 40)))


def get_hra_metro_percent() -> Decimal:
    """HRA for metro city employees = Basic × this%. Default 50."""
    return Decimal(str(_get('hra_percent_metro', 50)))


def get_hra_nonmetro_percent() -> Decimal:
    """HRA for non-metro employees = Basic × this%. Default 40."""
    return Decimal(str(_get('hra_percent_nonmetro', 40)))


def get_da_percent() -> Decimal:
    """DA = Basic × this%. Default 10. Fully dynamic from system settings."""
    return Decimal(str(_get('da_percent', 10)))


def get_pf_employee_percent() -> Decimal:
    """PF employee contribution % of Basic. Default 12."""
    return Decimal(str(_get('pf_employee_percent', 12)))


def get_pf_employer_percent() -> Decimal:
    """PF employer contribution % of Basic. Default 12."""
    return Decimal(str(_get('pf_employer_percent', 12)))


def get_esi_employee_percent() -> Decimal:
    """ESI employee contribution % of gross. Default 0.75."""
    return Decimal(str(_get('esi_employee_percent', 0.75)))


def get_esi_employer_percent() -> Decimal:
    """ESI employer contribution % of gross. Default 3.25."""
    return Decimal(str(_get('esi_employer_percent', 3.25)))


def get_esi_threshold() -> Decimal:
    """Gross salary above this = ESI exempt. Default 21000."""
    return Decimal(str(_get('esi_threshold_salary', 21000)))


def get_payroll_lock_day() -> int:
    """Payroll is available on day 1 of the next month for the previous month."""
    return 1


def get_tds_flat_contract() -> Decimal:
    """Flat TDS % for contract employees. Default 10."""
    return Decimal(str(_get('tds_flat_percent_contract', 10)))


def get_pt_flat_amount() -> Decimal:
    """
    Legacy flat Professional Tax amount.
    Kept as a fallback so existing settings/data continue to work.
    """
    return Decimal(str(_get('pt_flat_amount', 200)))


def get_pt_threshold_salary() -> Decimal:
    """Gross salary threshold for Professional Tax slabs. Default 15000."""
    return Decimal(str(_get('pt_threshold_salary', 15000)))


def get_pt_below_threshold_amount() -> Decimal:
    """PT amount when monthly gross is below/equal to threshold. Default 0."""
    return Decimal(str(_get('pt_below_threshold_amount', 0)))


def get_pt_above_threshold_amount() -> Decimal:
    """PT amount when monthly gross is above threshold. Falls back to legacy flat PT."""
    return Decimal(str(_get('pt_above_threshold_amount', get_pt_flat_amount())))


def calculate_professional_tax(gross) -> Decimal:
    """
    Professional Tax based on monthly gross salary.
    If gross <= pt_threshold_salary, use pt_below_threshold_amount.
    If gross > threshold, use pt_above_threshold_amount.
    """
    gross = Decimal(str(gross or 0))
    threshold = get_pt_threshold_salary()
    if gross <= threshold:
        return get_pt_below_threshold_amount()
    return get_pt_above_threshold_amount()


def get_pt_slabs() -> list:
    """
    Backward-compatible representation for clients that still expect slabs.
    """
    threshold = float(get_pt_threshold_salary())
    return [
        {'upto': threshold, 'pt': float(get_pt_below_threshold_amount())},
        {'above': threshold, 'pt': float(get_pt_above_threshold_amount())},
    ]


# ── LEAVE ─────────────────────────────────────────────────────────────────────

def get_leave_year_basis() -> str:
    return str(_get('leave_year_basis', 'calendar'))


def get_carry_forward_month() -> int:
    return int(_get('carry_forward_month', 1))


def get_half_day_leave_enabled() -> bool:
    return _parse_bool(_get('half_day_leave_enabled', True))


def get_leave_low_threshold() -> int:
    return int(_get('leave_balance_low_threshold', 2))


def get_sandwich_rule() -> bool:
    return _parse_bool(_get('sandwich_rule_enabled', True))


# ── PAYROLL FIXED ALLOWANCE DEFAULTS ─────────────────────────────────────────

def get_default_transport() -> Decimal:
    """Default transport allowance per month. Default 1600."""
    return Decimal(str(_get('default_transport_allowance', 1600)))


def get_default_medical() -> Decimal:
    """Default medical allowance per month. Default 1250."""
    return Decimal(str(_get('default_medical_allowance', 1250)))


def get_default_other_allowance() -> Decimal:
    """Default other allowance per month. Default 0."""
    return Decimal(str(_get('default_other_allowance', 0)))


def get_default_pt() -> Decimal:
    """Default professional tax per month. Falls back to gross-based PT above threshold."""
    return Decimal(str(_get('default_pt_amount', get_pt_above_threshold_amount())))


def get_working_days_per_month() -> int:
    """Standard working days per month for OT/LOP calculation. Default 22."""
    return int(_get('working_days_per_month', 22))


# ── GENERAL ───────────────────────────────────────────────────────────────────

def get_company_name() -> str:
    return str(_get('company_name', 'My Company'))


def get_currency() -> str:
    return str(_get('currency', 'INR'))


def get_fiscal_year_start_month() -> int:
    return int(_get('fiscal_year_start_month', 4))


def get_probation_months() -> int:
    return int(_get('probation_period_months', 6))




def get_sl_advance_notice_days() -> int:
    return int(_get('sl_advance_notice_days', 0))


def get_el_advance_notice_days() -> int:
    return int(_get('el_advance_notice_days', 0))


def get_leave_advance_notice_days(leave_code: str) -> int:
    code = (leave_code or '').upper()
    
    if code == 'SL':
        return get_sl_advance_notice_days()
    if code == 'EL':
        return get_el_advance_notice_days()
    key = f"{leave_code.lower()}_advance_notice_days"
    val = _get(key, None)
    if val is not None:
        try:
            return int(val)
        except (ValueError, TypeError):
            pass
    return 0


def get_leave_days_allowed(leave_code: str) -> int:
    code = (leave_code or '').lower()
    key  = f"{code}_days_per_year"
    val  = _get(key, None)
    if val is not None:
        try:
            return int(val)
        except (ValueError, TypeError):
            pass
    return -1


def get_leave_is_paid(leave_code: str) -> int:
    code = (leave_code or '').lower()
    key  = f"{code}_is_paid"
    val  = _get(key, None)
    if val is not None:
        if isinstance(val, bool):
            return 1 if val else 0
        if str(val).lower() in ('true', '1', 'yes'):
            return 1
        if str(val).lower() in ('false', '0', 'no'):
            return 0
    return -1


def get_leave_carry_forward(leave_code: str) -> int:
    code = (leave_code or '').lower()
    key  = f"{code}_carry_forward"
    val  = _get(key, None)
    if val is not None:
        if isinstance(val, bool):
            return 1 if val else 0
        if str(val).lower() in ('true', '1', 'yes'):
            return 1
        if str(val).lower() in ('false', '0', 'no'):
            return 0
    return -1
