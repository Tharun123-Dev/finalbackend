# payroll/engine.py
"""
Payroll Engine v4 — 100% dynamic from SystemSetting.
- Basic%, HRA%, DA%, PF%, ESI%, OT multiplier, PT slabs, TDS, Lock Day — ALL from settings_helper
- DA is now fully dynamic: read from da_percent system setting at runtime
- Working days uses weekend_days setting (5-day or 6-day week)
- LOP counted once as explicit deduction (no double-counting)
- PF/ESI/PT prorated by effective_present/working_days
- Full calculation breakdown stored per entry for payslip display

CALCULATION METHOD: Full-Pay + Explicit-LOP
  Step 1  Pay FULL monthly salary components (no proration of earnings).
  Step 2  Add OT pay (rate from overtime_multiplier setting).
  Step 3  LOP deduction = (structure.gross / working_days) × total_lop
  Step 4  Prorate PF, ESI, PT by (effective_present / working_days).
  Step 5  TDS on effective_gross (after LOP).
  Step 6  net_pay = gross − lop − pf − esi − pt − tds  (min 0).
  ALL rates read live from SystemSetting at runtime.
"""
import calendar
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from django.utils import timezone

from accounts.models import User
from attendance.models import AttendanceRecord
from attendance.settings_helper import (
    get_late_per_half_day, get_working_days_in_month, is_weekend,
    get_pf_employee_percent, get_pf_employer_percent,
    get_esi_employee_percent, get_esi_employer_percent, get_esi_threshold,
    get_tds_flat_contract, calculate_professional_tax, get_overtime_multiplier,
    get_da_percent, get_auto_absent_enabled,
)
from leave.models import LeaveRequest
from .models import (
    SalaryStructure, PayrollRun, PayrollEntry,
    PayrollAdjustment, PayrollCarryForwardAdjustment,
)


ROUND2 = lambda v: Decimal(str(v)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
COMP_OFF_CODES = {'COMP_OFF', 'COMP', 'CO', 'COMPENSATORY'}


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_active_structure(employee, as_of_date):
    qs = SalaryStructure.objects.filter(
        employee=employee,
        tenant_id=getattr(employee, 'tenant_id', 'default') or 'default',
        is_active=True,
        effective_date__lte=as_of_date,
    ).order_by('-effective_date')
    return qs.first() or SalaryStructure.objects.filter(
        employee=employee,
        tenant_id=getattr(employee, 'tenant_id', 'default') or 'default',
        is_active=True,
    ).order_by('effective_date').first()


def get_run_period(year, month, period_start=None, period_end=None):
    start_of_month = date(year, month, 1)
    end_of_month = date(year, month, calendar.monthrange(year, month)[1])
    return period_start or start_of_month, period_end or end_of_month


def count_working_days_between(start_date, end_date):
    total = 0
    cur = start_date
    while cur <= end_date:
        if not is_weekend(cur):
            total += 1
        cur += timedelta(days=1)
    return total


def get_period_factor(year, month, period_start, period_end):
    """Scale salary only for split payroll periods, using one working-day basis."""
    month_start = date(year, month, 1)
    month_end = date(year, month, calendar.monthrange(year, month)[1])
    full_month_working_days = count_working_days_between(month_start, month_end)
    period_working_days = count_working_days_between(period_start, period_end)
    if full_month_working_days <= 0:
        return Decimal('0'), period_working_days
    return (
        Decimal(str(period_working_days)) / Decimal(str(full_month_working_days)),
        period_working_days,
    )


def get_approved_leave_dates(employee, year, month, period_start=None, period_end=None):
    start_of_month, end_of_month = get_run_period(year, month, period_start, period_end)

    approved = LeaveRequest.objects.filter(
        employee=employee,
        tenant_id=getattr(employee, 'tenant_id', 'default') or 'default',
        status='approved',
        start_date__lte=end_of_month, end_date__gte=start_of_month,
    ).select_related('leave_type')

    paid_full_dates, paid_half_dates, lop_dates = set(), set(), set()

    for lr in approved:
        is_lop  = (not lr.leave_type.is_paid) or (lr.leave_type.code == 'LOP')
        is_half = lr.session in ('first_half', 'second_half')
        cur = lr.start_date
        while cur <= lr.end_date:
            if start_of_month <= cur <= end_of_month and not is_weekend(cur):
                if is_lop:
                    lop_dates.add(cur)
                elif is_half:
                    paid_half_dates.add(cur)
                else:
                    paid_full_dates.add(cur)
            cur += timedelta(days=1)

    return paid_full_dates, paid_half_dates, lop_dates


def calculate_late_lop(late_count: int) -> Decimal:
    late_per_half = get_late_per_half_day()
    half_units    = late_count // late_per_half
    return Decimal(str(half_units)) * Decimal('0.5')


def calculate_pt(gross: Decimal = None) -> Decimal:
    return ROUND2(calculate_professional_tax(gross))


def calculate_tds(effective_gross: Decimal, emp_type: str) -> Decimal:
    """TDS — dynamic contract rate from settings, slab for regular."""
    if emp_type == 'contract':
        rate = get_tds_flat_contract() / Decimal('100')
        return ROUND2(effective_gross * rate)
    if emp_type in ('intern', 'parttime'):
        return Decimal('0')
    annual = effective_gross * 12
    if annual <= Decimal('250000'):
        return Decimal('0')
    elif annual <= Decimal('500000'):
        return ROUND2((annual - Decimal('250000')) * Decimal('0.05') / 12)
    elif annual <= Decimal('1000000'):
        return ROUND2((Decimal('12500') + (annual - Decimal('500000')) * Decimal('0.20')) / 12)
    else:
        return ROUND2((Decimal('112500') + (annual - Decimal('1000000')) * Decimal('0.30')) / 12)


def calculate_ot_pay(basic: Decimal, working_days: int, ot_hours: Decimal) -> Decimal:
    """OT = (basic / working_days / hours_per_day) × ot_multiplier × ot_hours"""
    if working_days == 0 or ot_hours == 0:
        return Decimal('0')
    from attendance.settings_helper import get_standard_hours
    hours_per_day = Decimal(str(get_standard_hours()))
    multiplier    = get_overtime_multiplier()
    hourly_rate   = Decimal(str(basic)) / (Decimal(str(working_days)) * hours_per_day)
    return ROUND2(hourly_rate * multiplier * ot_hours)


def calculate_employee_payroll_values(emp, structure, year, month, period_start=None, period_end=None):
    _, days_in_month = get_working_days_in_month(year, month)
    period_start, period_end = get_run_period(year, month, period_start, period_end)
    period_factor, working_days = get_period_factor(year, month, period_start, period_end)
    att = get_attendance_summary(emp, year, month, period_start, period_end)
    present = att['present']
    lop_days = att['lop_days']
    late_lop = att['late_lop']
    total_lop = lop_days + late_lop
    ot_hours = att['ot_hours']
    extra_work_days = Decimal(str(att.get('extra_work_days', 0)))
    extra_work_dates = att.get('extra_work_dates', [])
    comp_off_days = Decimal(str(att.get('comp_off_days', 0)))

    effective_present = max(
        min(Decimal(str(working_days)) - total_lop, Decimal(str(working_days))),
        Decimal('0'),
    )

    pf_emp_pct = get_pf_employee_percent() / Decimal('100')
    esi_emp_pct = get_esi_employee_percent() / Decimal('100')
    esi_threshold = get_esi_threshold()
    da_pct_live = get_da_percent() / Decimal('100')

    basic = ROUND2(structure.basic * period_factor)
    hra = ROUND2(structure.hra * period_factor)
    da = ROUND2(basic * da_pct_live)
    transport = ROUND2(structure.transport * period_factor)
    medical = ROUND2(structure.medical * period_factor)
    other = ROUND2(structure.other_allowance * period_factor)

    monthly_ctc = ROUND2((Decimal(str(structure.ctc)) / Decimal('12')) * period_factor)
    special = ROUND2(monthly_ctc - basic - hra - da - transport - medical - other)
    special = max(special, Decimal('0'))

    ot_pay = calculate_ot_pay(basic, working_days, ot_hours)
    base_gross = basic + hra + da + special + transport + medical + other
    extra_work_pay = ROUND2((base_gross / Decimal(str(working_days))) * extra_work_days) if working_days > 0 else Decimal('0')
    gross = base_gross + ot_pay + extra_work_pay

    structure_gross = base_gross
    if working_days > 0 and total_lop > 0:
        per_day_rate = ROUND2(structure_gross / Decimal(str(working_days)))
        lop_deduction = ROUND2(per_day_rate * total_lop)
    else:
        lop_deduction = Decimal('0')
    lop_deduction = min(lop_deduction, structure_gross)

    effective_gross = max(ROUND2(gross - lop_deduction), Decimal('0'))
    ratio = (effective_present / Decimal(str(working_days))) if working_days > 0 else Decimal('0')

    pf_emp = ROUND2(basic * pf_emp_pct * ratio)
    esi_emp = ROUND2(effective_gross * esi_emp_pct * ratio) if effective_gross <= esi_threshold else Decimal('0')
    pt = ROUND2(calculate_pt(effective_gross) * ratio)
    tds = calculate_tds(effective_gross, emp.employee_type)

    total_deductions = ROUND2(pf_emp + esi_emp + pt + tds + lop_deduction)
    net_pay = max(ROUND2(gross - total_deductions), Decimal('0'))

    return {
        'att': att,
        'days_in_month': days_in_month,
        'working_days': working_days,
        'effective_present': effective_present,
        'total_lop': total_lop,
        'ot_hours': ot_hours,
        'extra_work_days': extra_work_days,
        'extra_work_dates': extra_work_dates,
        'comp_off_days': comp_off_days,
        'basic': basic,
        'hra': hra,
        'da': da,
        'special': special,
        'transport': transport,
        'medical': medical,
        'other': other,
        'ot_pay': ot_pay,
        'extra_work_pay': extra_work_pay,
        'gross': gross,
        'pf_emp': pf_emp,
        'esi_emp': esi_emp,
        'pt': pt,
        'tds': tds,
        'lop_deduction': lop_deduction,
        'total_deductions': total_deductions,
        'net_pay': net_pay,
    }


def queue_locked_regularization_adjustment(regularization):
    record = regularization.attendance
    source_run = PayrollRun.objects.filter(
        tenant_id=record.tenant_id,
        month=record.date.month,
        year=record.date.year,
        status='locked',
        period_start__lte=record.date,
        period_end__gte=record.date,
    ).first()
    if not source_run:
        return None

    old_entry = PayrollEntry.objects.filter(
        tenant_id=record.tenant_id,
        payroll_run=source_run,
        employee=record.employee,
    ).select_related('salary_structure').first()
    if not old_entry or not old_entry.salary_structure:
        return None

    values = calculate_employee_payroll_values(
        record.employee,
        old_entry.salary_structure,
        source_run.year,
        source_run.month,
    )
    existing = PayrollCarryForwardAdjustment.objects.filter(
        tenant_id=record.tenant_id,
        source_regularization=regularization,
        status='pending',
    ).first()
    total_delta = ROUND2(values['net_pay'] - old_entry.net_pay)
    already_queued = sum(
        item.amount
        for item in PayrollCarryForwardAdjustment.objects.filter(
            tenant_id=record.tenant_id,
            employee=record.employee,
            source_run=source_run,
        ).exclude(pk=existing.pk if existing else None).exclude(status='ignored')
    )
    delta = ROUND2(total_delta - already_queued)
    if delta == 0:
        if existing:
            existing.status = 'ignored'
            existing.amount = Decimal('0')
            existing.save(update_fields=['status', 'amount'])
        return None

    reason = (
        f"Attendance regularization approved for {record.date} "
        f"({record.shift_type} shift) after payroll {source_run.month}/{source_run.year} was locked. "
        f"Old net {old_entry.net_pay}, corrected net {values['net_pay']}."
    )
    if existing:
        existing.amount = delta
        existing.reason = reason
        existing.save(update_fields=['amount', 'reason'])
        return existing

    return PayrollCarryForwardAdjustment.objects.create(
        employee=record.employee,
        tenant_id=record.tenant_id,
        source_run=source_run,
        source_regularization=regularization,
        source_month=source_run.month,
        source_year=source_run.year,
        amount=delta,
        reason=reason,
    )


def apply_pending_carry_forward_adjustments(entry):
    pending = PayrollCarryForwardAdjustment.objects.filter(
        tenant_id=entry.tenant_id,
        employee=entry.employee,
        status='pending',
    ).exclude(
        source_year__gt=entry.payroll_run.year,
    ).exclude(
        source_year=entry.payroll_run.year,
        source_month__gte=entry.payroll_run.month,
    )

    changed_entry = False
    for item in pending:
        amount = ROUND2(item.amount)
        if amount == 0:
            item.status = 'ignored'
            item.applied_entry = entry
            item.applied_at = timezone.now()
            item.save(update_fields=['status', 'applied_entry', 'applied_at'])
            continue

        if amount > 0:
            adj_type = 'arrear'
            adj_amount = amount
            entry.gross = ROUND2(entry.gross + adj_amount)
            entry.net_pay = ROUND2(entry.net_pay + adj_amount)
            changed_entry = True
        else:
            adj_type = 'deduction'
            adj_amount = abs(amount)
            entry.total_deductions = ROUND2(entry.total_deductions + adj_amount)
            entry.net_pay = max(ROUND2(entry.net_pay - adj_amount), Decimal('0'))
            changed_entry = True

        PayrollAdjustment.objects.create(
            tenant_id=entry.tenant_id,
            payroll_entry=entry,
            type=adj_type,
            amount=adj_amount,
            reason=item.reason,
            added_by=None,
        )
        item.status = 'applied'
        item.applied_entry = entry
        item.applied_at = timezone.now()
        item.save(update_fields=['status', 'applied_entry', 'applied_at'])

    if changed_entry:
        entry.save(update_fields=['gross', 'total_deductions', 'net_pay'])


def count_comp_off_leave_days(employee, year, month, period_start=None, period_end=None):
    start_of_month, end_of_month = get_run_period(year, month, period_start, period_end)
    approved = LeaveRequest.objects.filter(
        employee=employee,
        tenant_id=getattr(employee, 'tenant_id', 'default') or 'default',
        status='approved',
        start_date__lte=end_of_month,
        end_date__gte=start_of_month,
        leave_type__code__in=COMP_OFF_CODES,
    ).select_related('leave_type')

    total = Decimal('0')
    for lr in approved:
        total += Decimal(str(lr.days))
    return total


def get_attendance_summary(employee, year, month, period_start=None, period_end=None):
    _, days_in_month = calendar.monthrange(year, month)
    period_start, period_end = get_run_period(year, month, period_start, period_end)

    records = AttendanceRecord.objects.filter(
        employee=employee,
        tenant_id=getattr(employee, 'tenant_id', 'default') or 'default',
        date__gte=period_start,
        date__lte=period_end,
    )

    try:
        from attendance.views import _refresh_record_from_current_policy
        for rec in records:
            original = (
                rec.shift_start_snapshot,
                rec.shift_end_snapshot,
                rec.grace_minutes_snapshot,
                rec.standard_hours_snapshot,
                rec.half_day_hours_snapshot,
                rec.is_overnight_shift,
                rec.check_in_at,
                rec.check_out_at,
                rec.hours_worked,
                rec.ot_hours,
                rec.status,
            )
            _refresh_record_from_current_policy(rec)
            updated = (
                rec.shift_start_snapshot,
                rec.shift_end_snapshot,
                rec.grace_minutes_snapshot,
                rec.standard_hours_snapshot,
                rec.half_day_hours_snapshot,
                rec.is_overnight_shift,
                rec.check_in_at,
                rec.check_out_at,
                rec.hours_worked,
                rec.ot_hours,
                rec.status,
            )
            if updated != original:
                rec.save(update_fields=[
                    'shift_start_snapshot',
                    'shift_end_snapshot',
                    'grace_minutes_snapshot',
                    'standard_hours_snapshot',
                    'half_day_hours_snapshot',
                    'is_overnight_shift',
                    'check_in_at',
                    'check_out_at',
                    'hours_worked',
                    'ot_hours',
                    'status',
                ])
    except Exception:
        pass

    record_map = {}
    for r in records:
        record_map.setdefault(r.date, []).append(r)
    from attendance.models import Holiday
    
    holiday_dates = set(
        Holiday.objects.filter(date__gte=period_start, date__lte=period_end)
        .filter(tenant_id=getattr(employee, 'tenant_id', 'default') or 'default')
        .values_list('date', flat=True)
    )
    paid_full_dates, paid_half_dates, lop_dates = (
        get_approved_leave_dates(employee, year, month, period_start, period_end)
    )
    comp_off_days = count_comp_off_leave_days(employee, year, month, period_start, period_end)

    present    = Decimal('0')
    lop        = Decimal('0')
    ot_hrs     = Decimal('0')
    late_count = 0
    extra_work_dates = []

    auto_absent_enabled = get_auto_absent_enabled()

    cur = period_start
    while cur <= period_end:
        d = cur

        if is_weekend(d):
            recs = record_map.get(d, [])
            for rec in recs:
                if rec.check_in and rec.check_out and str(rec.status).lower() in ('present', 'late', 'half_day'):
                    extra_work_dates.append({
                        'date': str(d),
                        'type': 'weekend',
                        'shift_type': getattr(rec, 'shift_type', 'day'),
                        'check_in': str(rec.check_in),
                        'check_out': str(rec.check_out),
                    })
                    if rec.ot_hours:
                        ot_hrs += Decimal(str(rec.ot_hours))
            cur += timedelta(days=1)
            continue

        recs = record_map.get(d, [])

        # ── PUBLIC HOLIDAY — checked FIRST, before any record or auto-absent logic ──
        # A holiday is always a full paid present day for ALL employees.
        # This applies even if:
        #   - the employee has no attendance record at all that month
        #   - the employee has a half_day / absent record on that date
        #   - auto_absent_enabled is True
        # OT is still counted if the employee chose to work on the holiday.
        if d in holiday_dates:
            present += Decimal('1')
            for rec in recs:
                if rec.check_in and rec.check_out and str(rec.status).lower() in ('present', 'late', 'half_day', 'holiday'):
                    extra_work_dates.append({
                        'date': str(d),
                        'type': 'holiday',
                        'shift_type': getattr(rec, 'shift_type', 'day'),
                        'check_in': str(rec.check_in),
                        'check_out': str(rec.check_out),
                    })
                    if rec.ot_hours:
                        ot_hrs += Decimal(str(rec.ot_hours))
            cur += timedelta(days=1)
            continue   # skip ALL record / auto-absent processing for this date

        if recs:
            day_present = Decimal('0')
            day_lop = Decimal('0')

            for rec in recs:
                status = str(rec.status).lower()

                if rec.check_in and not rec.check_out:
                    continue

                if status == 'present':
                    day_present = max(day_present, Decimal('1'))

                elif status == 'late':
                    day_present = max(day_present, Decimal('1'))
                    late_count += 1

                elif status == 'half_day':
                    if d in paid_full_dates or d in paid_half_dates:
                        day_present = max(day_present, Decimal('1'))
                    else:
                        day_present = max(day_present, Decimal('0.5'))
                        day_lop = max(day_lop, Decimal('0.5'))

                elif status == 'pending':
                    continue

                elif status in ['absent', 'auto_absent', 'lop']:
                    if d in paid_full_dates or d in paid_half_dates:
                        day_present = max(day_present, Decimal('1'))
                    elif auto_absent_enabled and day_present == 0:
                        day_lop = max(day_lop, Decimal('1'))

                elif status in ('leave', 'lop_leave'):
                    if d in lop_dates:
                        day_lop = max(day_lop, Decimal('1'))
                    else:
                        day_present = max(day_present, Decimal('1'))

                elif status == 'holiday':
                    day_present = max(day_present, Decimal('1'))

                if (
                    rec.check_in
                    and rec.check_out
                    and status in ('present', 'late', 'half_day', 'holiday')
                    and rec.ot_hours
                ):
                    ot_hrs += Decimal(str(rec.ot_hours))

            present += day_present
            if day_present < Decimal('1'):
                lop += day_lop

        else:
            # No attendance record, not a holiday, not a weekend
            if d in paid_full_dates or d in paid_half_dates:
                present += Decimal('1')
            elif d in lop_dates:
                lop += Decimal('1')
            else:
                if auto_absent_enabled:
                    lop += Decimal('1')

        cur += timedelta(days=1)

    late_lop = calculate_late_lop(late_count)

    raw_extra_days = Decimal(str(len(extra_work_dates)))
    paid_extra_days = max(raw_extra_days - comp_off_days, Decimal('0'))
    paid_extra_date_count = int(paid_extra_days)
    for idx, item in enumerate(extra_work_dates):
        item['payable'] = idx < paid_extra_date_count

    # Count holidays this month for display in payslip attendance section
    from attendance.models import Holiday as _Holiday
    holiday_count = _Holiday.objects.filter(
        tenant_id=getattr(employee, 'tenant_id', 'default') or 'default',
        date__gte=period_start,
        date__lte=period_end,
    ).count()
    holiday_names = list(
        _Holiday.objects.filter(
            tenant_id=getattr(employee, 'tenant_id', 'default') or 'default',
            date__gte=period_start,
            date__lte=period_end,
        )
        .values_list('name', flat=True)
    )

    return {
        'present':       present,
        'lop_days':      lop,
        'late_lop':      late_lop,
        'late_count':    late_count,
        'ot_hours':      ot_hrs,
        'holiday_count': holiday_count,
        'holiday_names': holiday_names,
        'extra_work_days': paid_extra_days,
        'extra_work_dates': extra_work_dates,
        'comp_off_days': comp_off_days,
    }


# ── Main Engine ───────────────────────────────────────────────────────────────

def process_payroll_run(payroll_run: PayrollRun, employee_ids=None):
    """
    All 11 payroll settings read live from SystemSetting at runtime:
    1. basic_salary_percent  — not used in engine (used at salary structure creation)
    2. hra_percent_metro / hra_percent_nonmetro — stored in SalaryStructure.hra_percent
    3. da_percent            — READ LIVE from settings each run (overrides structure value)
    4. pf_employee_percent   — READ LIVE
    5. pf_employer_percent   — informational / CTC
    6. esi_employee_percent  — READ LIVE
    7. esi_employer_percent  — informational / CTC
    8. esi_threshold_salary  — READ LIVE (eligibility gate)
    9. payroll_lock_day      — enforced in views/frontend
    10. tds_flat_percent_contract — READ LIVE
    11. pt_slab_json         — READ LIVE

    DA is always recalculated from current da_percent system setting
    (not from the stored structure.da_percent) so changing DA% in
    System Settings reflects in the very next payroll run.
    """
    month = payroll_run.month
    year  = payroll_run.year
    _, days_in_month = get_working_days_in_month(year, month)
    period_start, period_end = get_run_period(
        year, month, payroll_run.period_start, payroll_run.period_end
    )
    period_factor, working_days = get_period_factor(year, month, period_start, period_end)
    as_of = period_end

    # ── Read ALL live rates from System Settings ──────────────────────
    pf_emp_pct    = get_pf_employee_percent()  / Decimal('100')
    esi_emp_pct   = get_esi_employee_percent() / Decimal('100')
    esi_threshold = get_esi_threshold()
    da_pct_live   = get_da_percent() / Decimal('100')   # DA from settings, NOT structure

    employees = User.objects.filter(is_active=True, tenant_id=payroll_run.tenant_id)
    if employee_ids:
        employees = employees.filter(id__in=employee_ids)
    created, skipped = [], []

    for emp in employees:
        if PayrollEntry.objects.filter(payroll_run=payroll_run, employee=emp, tenant_id=payroll_run.tenant_id).exists():
            continue

        structure = get_active_structure(emp, as_of)
        if not structure:
            skipped.append(emp.username)
            continue

        # ── Attendance ────────────────────────────────────────────────
        att           = get_attendance_summary(emp, year, month, period_start, period_end)
        present       = att['present']
        lop_days      = att['lop_days']
        late_lop      = att['late_lop']
        late_count    = att['late_count']
        ot_hours      = att['ot_hours']
        holiday_count = att.get('holiday_count', 0)
        holiday_names = att.get('holiday_names', [])
        extra_work_days = Decimal(str(att.get('extra_work_days', 0)))
        extra_work_dates = att.get('extra_work_dates', [])
        comp_off_days = Decimal(str(att.get('comp_off_days', 0)))
        total_lop     = lop_days + late_lop

        effective_present = max(
            min(Decimal(str(working_days)) - total_lop, Decimal(str(working_days))),
            Decimal('0'),
        )

        # ── Step 1: Full monthly earnings ─────────────────────────────
        # Basic and HRA are from the salary structure (set at creation time)
        basic     = ROUND2(structure.basic * period_factor)
        hra       = ROUND2(structure.hra * period_factor)

        # DA: LIVE from system setting — changing da_percent in System Settings
        # takes effect on the very next payroll run without editing salary structure
        da        = ROUND2(basic * da_pct_live)

        transport = ROUND2(structure.transport * period_factor)
        medical   = ROUND2(structure.medical * period_factor)
        other     = ROUND2(structure.other_allowance * period_factor)

        # Special allowance = CTC monthly − all named components
        monthly_ctc = ROUND2((Decimal(str(structure.ctc)) / Decimal('12')) * period_factor)
        special = ROUND2(
            monthly_ctc - basic - hra - da - transport - medical - other
        )
        special = max(special, Decimal('0'))  # never negative

        # ── Step 2: OT pay ────────────────────────────────────────────
        ot_pay = calculate_ot_pay(basic, working_days, ot_hours)
        base_gross = basic + hra + da + special + transport + medical + other
        extra_work_pay = ROUND2((base_gross / Decimal(str(working_days))) * extra_work_days) if working_days > 0 else Decimal('0')
        gross  = base_gross + ot_pay + extra_work_pay

        # ── Step 3: LOP deduction ─────────────────────────────────────
        structure_gross = base_gross  # exclude OT and extra-work pay from LOP base
        if working_days > 0 and total_lop > 0:
            per_day_rate  = ROUND2(structure_gross / Decimal(str(working_days)))
            lop_deduction = ROUND2(per_day_rate * total_lop)
        else:
            lop_deduction = Decimal('0')
        lop_deduction = min(lop_deduction, structure_gross)

        effective_gross = max(ROUND2(gross - lop_deduction), Decimal('0'))

        # ── Step 4: Prorate statutory deductions ──────────────────────
        ratio = (effective_present / Decimal(str(working_days))) if working_days > 0 else Decimal('0')

        # PF: live % of basic (prorated by attendance ratio)
        pf_emp  = ROUND2(basic * pf_emp_pct * ratio)

        # ESI: live % of effective gross, only if gross <= threshold (prorated)
        esi_emp = ROUND2(effective_gross * esi_emp_pct * ratio) if effective_gross <= esi_threshold else Decimal('0')

        # PT: ALWAYS use pt_flat_amount from System Settings.
        # Changing PT in System Settings → takes effect on the very next payroll run.
        # Structure's stored pt is ignored — single source of truth is System Settings.
        pt_full = calculate_pt(effective_gross)
        pt      = ROUND2(pt_full * ratio)

        # ── Step 5: TDS ───────────────────────────────────────────────
        tds = calculate_tds(effective_gross, emp.employee_type)

        # ── Step 6: Net pay ───────────────────────────────────────────
        total_deductions = ROUND2(pf_emp + esi_emp + pt + tds + lop_deduction)
        net_pay          = max(ROUND2(gross - total_deductions), Decimal('0'))

        entry = PayrollEntry.objects.create(
            tenant_id         = payroll_run.tenant_id,
            payroll_run       = payroll_run,
            employee          = emp,
            salary_structure  = structure,
            total_days        = (period_end - period_start).days + 1,
            working_days      = working_days,
            present_days      = effective_present,
            lop_days          = total_lop,
            ot_hours          = ot_hours,
            holiday_count     = holiday_count,
            holiday_names     = holiday_names,
            extra_work_days   = extra_work_days,
            extra_work_pay    = extra_work_pay,
            extra_work_dates  = extra_work_dates,
            comp_off_days     = comp_off_days,
            basic             = basic,
            hra               = hra,
            da                = da,
            special_allowance = special,
            transport         = transport,
            medical           = medical,
            other_allowance   = other,
            ot_pay            = ot_pay,
            pf_employee       = pf_emp,
            esi_employee      = esi_emp,
            pt                = pt,
            tds               = tds,
            lop_deduction     = lop_deduction,
            gross             = gross,
            total_deductions  = total_deductions,
            net_pay           = net_pay,
        )
        apply_pending_carry_forward_adjustments(entry)
        created.append(entry)

    return created, skipped
