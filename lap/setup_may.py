# setup_may.py
# ═══════════════════════════════════════════════════════════════
# Creates a realistic May 2026 scenario with:
#   - 2 employees (EMP001 regular, EMP002 contract)
#   - Salary structures for both
#   - Full month attendance (present, absent, half-day, OT)
#   - Leave requests (CL approved, SL approved, LOP approved, one rejected)
#   - Payroll run → process → approve
# ═══════════════════════════════════════════════════════════════

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lap.settings')
django.setup()
from datetime import date, time, timedelta
from decimal import Decimal

from accounts.models import User
from employees.models import Department, EmployeeProfile
from attendance.models import AttendanceRecord
from leave.models import LeaveType, LeaveBalance, LeaveRequest
from payroll.models import SalaryStructure, PayrollRun, PayrollEntry
from utils.models import Permission, RolePermission

YEAR  = 2026
MONTH = 5   # May

print("═" * 60)
print("STEP 1 — Clean previous May 2026 data")
print("═" * 60)

PayrollEntry.objects.filter(payroll_run__month=MONTH, payroll_run__year=YEAR).delete()
PayrollRun.objects.filter(month=MONTH, year=YEAR).delete()
AttendanceRecord.objects.filter(date__year=YEAR, date__month=MONTH).delete()
LeaveRequest.objects.filter(start_date__year=YEAR, start_date__month=MONTH).delete()
print("✓ Cleared")

# ─────────────────────────────────────────────────────────────
print("\nSTEP 2 — Ensure departments exist")
dept, _ = Department.objects.get_or_create(
    name='Engineering',
    defaults={'description': 'Software team'}
)
print(f"✓ Dept: {dept.name}")

# ─────────────────────────────────────────────────────────────
print("\nSTEP 3 — Ensure employees exist")

def get_or_create_emp(username, first, last, emp_code, role, emp_type, password='Test@1234'):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name':    first,
            'last_name':     last,
            'email':         f'{username}@lap.com',
            'role':          role,
            'employee_type': emp_type,
        }
    )
    if created:
        user.set_password(password)
        user.save()

    profile, _ = EmployeeProfile.objects.get_or_create(
        user=user,
        defaults={
            'emp_code':    emp_code,
            'department':  dept,
            'designation': 'software_engineer',
            'joining_date': date(2025, 1, 1),
        }
    )
    return user

emp1 = get_or_create_emp('john.doe',  'John',  'Doe',   'EMP001', 'employee', 'regular')
emp2 = get_or_create_emp('jane.smith','Jane',  'Smith', 'EMP002', 'employee', 'contract')
print(f"✓ {emp1.get_full_name()} (EMP001 regular)")
print(f"✓ {emp2.get_full_name()} (EMP002 contract)")

# ─────────────────────────────────────────────────────────────
print("\nSTEP 4 — Salary structures")

def ensure_salary(emp, ctc, basic, hra, da, special, transport, medical, pf_emp, pt):
    SalaryStructure.objects.filter(employee=emp, is_active=True).update(is_active=False)
    s = SalaryStructure.objects.create(
        employee          = emp,
        effective_date    = date(2026, 1, 1),
        ctc               = ctc,
        basic             = basic,
        hra               = hra,
        da                = da,
        special_allowance = special,
        transport         = transport,
        medical           = medical,
        other_allowance   = 0,
        pf_employee       = pf_emp,
        esi_employee      = 0,
        pt                = pt,
        pf_employer       = pf_emp,
        esi_employer      = 0,
        is_active         = True,
    )
    gross = s.gross
    print(f"  {emp.username}: CTC={ctc} | Gross={gross} | PF={pf_emp} | PT={pt} | Net(full)={gross - pf_emp - pt}")
    return s

# EMP001: Annual CTC 7,20,000 → Monthly gross 51,250
s1 = ensure_salary(emp1,
    ctc=720000, basic=24000, hra=12000, da=2400,
    special=10000, transport=1600, medical=1250,
    pf_emp=2880, pt=200
)
# EMP002: Contract, fixed 40,000/month
s2 = ensure_salary(emp2,
    ctc=480000, basic=30000, hra=0, da=0,
    special=8000, transport=1200, medical=800,
    pf_emp=0, pt=0
)
print("✓ Salary structures created")

# ─────────────────────────────────────────────────────────────
print("\nSTEP 5 — Ensure leave types")

leave_types_data = [
    ('Casual Leave',      'CL',   12, 'all',     False, True,  0),
    ('Sick Leave',        'SL',   12, 'all',     False, True,  0),
    ('Earned Leave',      'EL',   15, 'regular', True,  True,  7),
    ('Loss of Pay',       'LOP', 365, 'all',     False, False, 0),
    ('Maternity Leave',   'ML',  182, 'regular', False, True,  30),
    ('Compensatory Off',  'COMP',  5, 'all',     True,  True,  1),
]
for name, code, days, app, cf, paid, notice in leave_types_data:
    lt, _ = LeaveType.objects.get_or_create(
        code=code,
        defaults={
            'name': name, 'days_allowed': days,
            'applicable_to': app, 'carry_forward': cf,
            'is_paid': paid, 'min_notice_days': notice,
            'is_active': True,
        }
    )

lt_cl  = LeaveType.objects.get(code='CL')
lt_sl  = LeaveType.objects.get(code='SL')
lt_lop = LeaveType.objects.get(code='LOP')
print("✓ Leave types ready")

# ─────────────────────────────────────────────────────────────
print("\nSTEP 6 — Init leave balances")

for emp in [emp1, emp2]:
    for lt in LeaveType.objects.filter(is_active=True):
        if lt.applicable_to not in ('all', emp.employee_type):
            continue
        LeaveBalance.objects.get_or_create(
            employee=emp, leave_type=lt, year=YEAR,
            defaults={'total': lt.days_allowed}
        )
print("✓ Leave balances initialised")

# ─────────────────────────────────────────────────────────────
print("\nSTEP 7 — Create leave requests for May 2026")

# Get admin to approve
admin = User.objects.filter(role__in=['superadmin','admin']).first()
if not admin:
    admin = emp1  # fallback

def apply_leave(emp, lt, start, end, reason, auto_status='approved'):
    # Count working days
    days = 0
    cur = start
    while cur <= end:
        if cur.weekday() < 5:
            days += 1
        cur += timedelta(days=1)

    lr = LeaveRequest.objects.create(
        employee   = emp,
        leave_type = lt,
        start_date = start,
        end_date   = end,
        days       = days,
        session    = 'full',
        reason     = reason,
        status     = 'pending',
    )

    if auto_status == 'approved':
        lr.status      = 'approved'
        lr.approved_by = admin
        lr.save()
        # Update balance
        bal, _ = LeaveBalance.objects.get_or_create(
            employee=emp, leave_type=lt, year=YEAR,
            defaults={'total': lt.days_allowed}
        )
        bal.used    = Decimal(str(bal.used)) + Decimal(str(days))
        bal.pending = max(Decimal(str(bal.pending)) - Decimal(str(days)), Decimal('0'))
        bal.save()

    elif auto_status == 'rejected':
        lr.status       = 'rejected'
        lr.approved_by  = admin
        lr.approver_note = 'Insufficient reason'
        lr.save()

    return lr

# EMP001 scenarios:
# • 2 days CL (May 5-6) → APPROVED → paid leave, no LOP
lr1 = apply_leave(emp1, lt_cl, date(2026,5,5), date(2026,5,6), "Family function", 'approved')
print(f"  ✓ EMP001 CL May 5-6 → APPROVED ({lr1.days} days)")

# • 1 day SL (May 14) → REJECTED → absence recorded, will be LOP
lr2 = apply_leave(emp1, lt_sl, date(2026,5,14), date(2026,5,14), "Fever", 'rejected')
print(f"  ✓ EMP001 SL May 14 → REJECTED (becomes LOP)")

# • 1 day LOP (May 21) → APPROVED → explicit LOP deduction
lr3 = apply_leave(emp1, lt_lop, date(2026,5,21), date(2026,5,21), "Personal work", 'approved')
print(f"  ✓ EMP001 LOP May 21 → APPROVED ({lr3.days} days)")

# EMP002 scenarios:
# • 3 days SL (May 19-21) → APPROVED
lr4 = apply_leave(emp2, lt_sl, date(2026,5,19), date(2026,5,21), "Medical leave", 'approved')
print(f"  ✓ EMP002 SL May 19-21 → APPROVED ({lr4.days} days)")

# ─────────────────────────────────────────────────────────────
print("\nSTEP 8 — Create attendance records for May 2026")

from datetime import date as date_type
import calendar as cal_mod

def make_att(emp, d, status, ci=None, co=None, hours=0, ot=0, wfh=False):
    AttendanceRecord.objects.update_or_create(
        employee=emp, date=d,
        defaults={
            'check_in':     ci,
            'check_out':    co,
            'hours_worked': hours,
            'ot_hours':     ot,
            'status':       status,
            'is_wfh':       wfh,
        }
    )

_, days_in_may = cal_mod.monthrange(YEAR, MONTH)

# ── EMP001 attendance ─────────────────────────────────────────
print("  Building EMP001 attendance...")
for day in range(1, days_in_may + 1):
    d = date_type(YEAR, MONTH, day)
    if d.weekday() >= 5:
        continue  # skip weekends

    if d in (date_type(2026,5,5), date_type(2026,5,6)):
        make_att(emp1, d, 'leave')           # CL approved
    elif d == date_type(2026,5,8):
        make_att(emp1, d, 'late',            # late arrival
            ci=time(9,35), co=time(18,0), hours=8.4)
    elif d == date_type(2026,5,12):
        make_att(emp1, d, 'half_day',        # half day
            ci=time(9,0), co=time(13,0), hours=4)
    elif d == date_type(2026,5,14):
        make_att(emp1, d, 'absent')          # SL rejected → absent → LOP
    elif d == date_type(2026,5,15):
        make_att(emp1, d, 'present',         # OT day
            ci=time(9,0), co=time(20,0), hours=11, ot=3)
    elif d == date_type(2026,5,21):
        make_att(emp1, d, 'absent')          # LOP leave approved — handled via leave module
    elif d == date_type(2026,5,22):
        make_att(emp1, d, 'present',
            ci=time(9,0), co=time(18,0), hours=8, wfh=True)
    elif day <= days_in_may:
        make_att(emp1, d, 'present',
            ci=time(9,0), co=time(18,0), hours=8)

# ── EMP002 attendance ─────────────────────────────────────────
print("  Building EMP002 attendance...")
for day in range(1, days_in_may + 1):
    d = date_type(YEAR, MONTH, day)
    if d.weekday() >= 5:
        continue

    if d in (date_type(2026,5,19), date_type(2026,5,20), date_type(2026,5,21)):
        make_att(emp2, d, 'leave')           # SL approved
    elif d == date_type(2026,5,7):
        make_att(emp2, d, 'absent')          # plain absent → LOP
    elif d == date_type(2026,5,13):
        make_att(emp2, d, 'present',         # OT day
            ci=time(9,0), co=time(21,0), hours=12, ot=4)
    else:
        make_att(emp2, d, 'present',
            ci=time(9,0), co=time(18,0), hours=8)

att1 = AttendanceRecord.objects.filter(employee=emp1, date__year=YEAR, date__month=MONTH).count()
att2 = AttendanceRecord.objects.filter(employee=emp2, date__year=YEAR, date__month=MONTH).count()
print(f"  ✓ EMP001: {att1} records  |  EMP002: {att2} records")

# ─────────────────────────────────────────────────────────────
print("\nSTEP 9 — Process payroll run for May 2026")

from payroll.engine import process_payroll_run, attendance_summary, working_days_in_month

run = PayrollRun.objects.create(
    month        = MONTH,
    year         = YEAR,
    status       = 'draft',
    processed_by = admin,
    notes        = 'May 2026 — test run',
)

created, skipped = process_payroll_run(run)
run.status = 'processed'
run.save()

print(f"  ✓ Processed: {len(created)} entries | Skipped: {skipped}")

# ─────────────────────────────────────────────────────────────
print("\nSTEP 10 — Show payroll results BEFORE approving")
print("─" * 60)

for entry in PayrollEntry.objects.filter(payroll_run=run).select_related('employee'):
    e  = entry
    nm = e.employee.get_full_name()
    print(f"\n  {nm} ({e.employee.employee_type})")
    print(f"    Working days   : {e.working_days}")
    print(f"    Present days   : {float(e.present_days)}")
    print(f"    LOP days       : {float(e.lop_days)}")
    print(f"    OT hours       : {float(e.ot_hours)}")
    print(f"    Gross          : ₹{float(e.gross):,.2f}")
    print(f"    PF             : ₹{float(e.pf_employee):,.2f}")
    print(f"    ESI            : ₹{float(e.esi_employee):,.2f}")
    print(f"    PT             : ₹{float(e.pt):,.2f}")
    print(f"    TDS            : ₹{float(e.tds):,.2f}")
    print(f"    LOP deduction  : ₹{float(e.lop_deduction):,.2f}  ← display only")
    print(f"    Total deduct   : ₹{float(e.total_deductions):,.2f}")
    print(f"    NET PAY        : ₹{float(e.net_pay):,.2f}")

    s = e.salary_structure
    wdays = e.working_days
    print(f"\n    Cross-check:")
    print(f"    Structure gross: ₹{float(s.gross):,.2f}")
    print(f"    Pro-ration      : {float(e.present_days)}/{wdays} = {float(e.present_days)/wdays:.4f}")
    expected_gross = float(s.gross) * float(e.present_days) / wdays
    print(f"    Expected gross : ₹{expected_gross:,.2f}")
    print(f"    Actual gross   : ₹{float(e.gross):,.2f}")
    diff = abs(expected_gross - float(e.gross))
    print(f"    Match          : {'✅' if diff < 1 else f'❌ diff={diff:.2f}'}")

print("\n" + "─" * 60)
print("Setup complete. Run check_may.py to verify all details.")
print("Run approve_may.py to approve and lock payroll.")