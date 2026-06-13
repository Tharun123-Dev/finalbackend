# attendance/management/commands/mark_absent.py
"""
Management command: mark_absent
--------------------------------
Two jobs in one command (runs at midnight every weekday):

JOB 1 — Missing check-out (previous working day):
  If an employee checked IN yesterday but never checked OUT,
  update yesterday's record to status='half_day' and hours_worked=0
  so payroll deducts exactly 0.5 LOP for that day.

JOB 2 — No check-in at all (today):
  Employees with zero attendance record for today →
  mark absent so payroll counts it as 1 LOP.

Cron (runs at 00:05 every weekday — just after midnight):
    5 0 * * 1-5 /path/to/venv/bin/python /path/to/manage.py mark_absent

Skips weekends (settings-based), public holidays, employees on approved leave.

FIX: Weekend detection now uses settings_helper.is_weekend() instead of
     hardcoded weekday() >= 5.  Supports 5-day and 6-day work weeks.
"""

from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from attendance.models import AttendanceRecord, Holiday
from leave.models import LeaveRequest


def get_prev_working_day(d):
    """Return the most recent working day before d (respects settings-based weekends)."""
    from attendance.settings_helper import is_weekend
    prev = d - timedelta(days=1)
    while is_weekend(prev):
        prev -= timedelta(days=1)
    return prev

class Command(BaseCommand):
    help = (
        'Auto-mark attendance:\n'
        '- Missing checkout yesterday → ABSENT (1 full LOP)\n'
        '- No check-in today → ABSENT (1 full LOP)\n'
        '- Skips weekends, holidays, approved leaves\n'
        '- Fully dynamic using System Settings'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            default=None,
            help='Date to process as TODAY (YYYY-MM-DD). Defaults to today.',
        )

    def handle(self, *args, **options):

        from attendance.settings_helper import (
            is_weekend,
            get_auto_absent_enabled,
        )

        raw = options.get('date')
        today = date.fromisoformat(raw) if raw else date.today()

        # Dynamic setting
        auto_absent_enabled = get_auto_absent_enabled()

        # Auto absent disabled
        if not auto_absent_enabled:
            self.stdout.write(
                'Auto absent disabled from System Settings.'
            )
            return

        # Skip weekends
        if is_weekend(today):
            self.stdout.write(
                f'{today} is a weekend — nothing to do.'
            )
            return

        # Skip public holiday
        if Holiday.objects.filter(date=today).exists():
            self.stdout.write(
                f'{today} is a public holiday — nothing to do.'
            )
            return

        yesterday = get_prev_working_day(today)

        employees = User.objects.filter(
            is_active=True
        )

        # Employees already on approved leave
        on_leave_today = set(
            LeaveRequest.objects.filter(
                status='approved',
                start_date__lte=today,
                end_date__gte=today,
            ).values_list('employee_id', flat=True)
        )

        # Existing attendance today
        already_marked_today = set(
            AttendanceRecord.objects.filter(
                date=today
            ).values_list('employee_id', flat=True)
        )

        open_shift_employee_ids = set()
        for rec in AttendanceRecord.objects.filter(
            check_in__isnull=False,
            check_out__isnull=True,
            date__lte=today,
        ).select_related('employee'):
            expected_end = rec.expected_shift_end_at()
            if expected_end and timezone.localtime(timezone.now()) <= expected_end:
                open_shift_employee_ids.add(rec.employee_id)

        # ─────────────────────────────────────────────
        # JOB 1
        # Missing checkout yesterday → FULL ABSENT
        # ─────────────────────────────────────────────

        incomplete_yesterday = AttendanceRecord.objects.filter(
            date=yesterday,
            check_in__isnull=False,
            check_out__isnull=True,
        ).select_related('employee')

        job1_marked = 0

        for rec in incomplete_yesterday:

            emp = rec.employee

            if not emp.is_active:
                continue

            expected_end = rec.expected_shift_end_at()
            if expected_end and timezone.localtime(timezone.now()) <= expected_end:
                self.stdout.write(
                    f'  [SKIP - OPEN NIGHT SHIFT] '
                    f'{emp.get_full_name() or emp.username} '
                    f'expected checkout after {timezone.localtime(expected_end).strftime("%Y-%m-%d %H:%M")}'
                )
                continue

            rec.status = 'pending'
            rec.hours_worked = 0
            rec.ot_hours = 0

            rec.note = (
                rec.note + ' | '
                if rec.note else ''
            ) + (
                'PENDING CORRECTION: missing checkout'
            )

            rec.save(update_fields=[
                'status',
                'hours_worked',
                'ot_hours',
                'note',
            ])

            job1_marked += 1

            self.stdout.write(
                f'  [PENDING] '
                f'{emp.get_full_name() or emp.username} '
                f'— missing checkout on {yesterday} '
                f'→ PENDING'
            )

        # ─────────────────────────────────────────────
        # JOB 2
        # No check-in today → ABSENT
        # ─────────────────────────────────────────────

        job2_marked = 0

        for emp in employees:

            # Skip approved leave
            if emp.id in on_leave_today:

                self.stdout.write(
                    f'  [SKIP — ON LEAVE] '
                    f'{emp.get_full_name() or emp.username}'
                )

                continue

            # Already has attendance
            if emp.id in already_marked_today:
                continue

            if emp.id in open_shift_employee_ids:
                self.stdout.write(
                    f'  [SKIP - OPEN SHIFT] '
                    f'{emp.get_full_name() or emp.username}'
                )
                continue

            AttendanceRecord.objects.update_or_create(
                employee=emp,
                date=today,
                shift_type='day',
                defaults={
                    'status': 'pending',
                    'hours_worked': 0,
                    'ot_hours': 0,
                    'note': (
                        'PENDING CORRECTION: '
                        'no check-in recorded'
                    ),
                },
            )

            job2_marked += 1

            self.stdout.write(
                f'  [PENDING] '
                f'{emp.get_full_name() or emp.username} '
                f'— no check-in today '
                f'→ PENDING'
            )

        # ─────────────────────────────────────────────
        # FINAL SUMMARY
        # ─────────────────────────────────────────────

        self.stdout.write(
            self.style.SUCCESS(
                f'\n{today} completed:\n'
                f'  Missing checkout → {job1_marked} pending\n'
                f'  No check-in      → {job2_marked} pending\n'
                f'  Total marked     → {job1_marked + job2_marked}'
            )
        )
