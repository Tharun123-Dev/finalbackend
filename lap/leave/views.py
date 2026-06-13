# leave/views.py
from datetime import date, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.shortcuts import get_object_or_404

from utils.permissions import make_permission, make_any_permission, IsAuthenticatedUser
from accounts.tenant_utils import get_tenant_id
from accounts.models import User
from .models import LeaveType, LeaveBalance, LeaveRequest
from .serializers import LeaveTypeSerializer, LeaveBalanceSerializer, LeaveRequestSerializer
from .utils import (
    count_working_days, get_or_create_balance,
    init_balances_for_employee, process_carry_forward,
    get_leave_balance_summary, sync_balances_for_leave_type,
)

COMP_OFF_CODES = {'COMP_OFF', 'COMP', 'CO', 'COMPENSATORY'}


def _is_comp_off_type(leave_type):
    return (leave_type.code or '').upper() in COMP_OFF_CODES


def _blocked_leave_dates(start, end):
    from attendance.models import Holiday
    from attendance.settings_helper import is_weekend

    holiday_map = {
        h.date: h.name
        for h in Holiday.objects.filter(date__gte=start, date__lte=end)
    }
    blocked = []
    cur = start
    while cur <= end:
        if cur in holiday_map:
            blocked.append({'date': cur, 'type': 'holiday', 'label': holiday_map[cur]})
        elif is_weekend(cur):
            blocked.append({'date': cur, 'type': 'week off', 'label': 'Week off'})
        cur += timedelta(days=1)
    return blocked


def _comp_off_work_summary(employee, leave=None):
    from attendance.models import AttendanceRecord, Holiday
    from attendance.settings_helper import is_weekend

    worked = []
    qs = AttendanceRecord.objects.filter(
        employee=employee,
        check_in__isnull=False,
        check_out__isnull=False,
        status__in=['present', 'late', 'half_day', 'holiday'],
    ).order_by('date')

    for rec in qs:
        is_holiday = Holiday.objects.filter(date=rec.date).exists()
        if is_weekend(rec.date) or is_holiday:
            worked.append({
                'date': str(rec.date),
                'type': 'holiday' if is_holiday else 'weekend',
                'check_in': str(rec.check_in),
                'check_out': str(rec.check_out),
            })

    used_qs = LeaveRequest.objects.filter(
        employee=employee,
        status__in=['approved', 'pending'],
        leave_type__code__in=COMP_OFF_CODES,
    )
    if leave:
        used_qs = used_qs.exclude(pk=leave.pk)

    used_days = sum(float(r.days) for r in used_qs)
    available = max(len(worked) - used_days, 0)
    return {
        'worked_days': len(worked),
        'used_or_pending_days': used_days,
        'available_days': available,
        'worked_dates': worked,
    }


# ── LEAVE TYPES ───────────────────────────────────────────────────────────────

class LeaveTypeListCreateView(generics.ListCreateAPIView):
    serializer_class = LeaveTypeSerializer

    def get_queryset(self):
        return LeaveType.objects.filter(is_active=True, tenant_id=get_tenant_id(self.request))

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticatedUser()]
        return [make_permission('configure_leave')()]

    def perform_create(self, serializer):
        """After creating a new leave type, auto-create balance rows for all employees."""
        leave_type = serializer.save(tenant_id=get_tenant_id(self.request))
        year       = date.today().year
        result     = sync_balances_for_leave_type(leave_type, year)
        # Store sync result so create() can include it in the response
        self._sync_result = result

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        resp_data = dict(serializer.data)
        resp_data['balance_sync'] = getattr(self, '_sync_result', {})
        return Response(resp_data, status=status.HTTP_201_CREATED, headers=headers)


class LeaveTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LeaveTypeSerializer

    def get_queryset(self):
        return LeaveType.objects.filter(tenant_id=get_tenant_id(self.request))

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticatedUser()]
        return [make_permission('configure_leave')()]

    def perform_update(self, serializer):
        """
        After updating a leave type, if days_allowed changed → sync all
        existing LeaveBalance rows so totals reflect the new allocation.
        """
        old_days = self.get_object().days_allowed
        leave_type = serializer.save()
        if leave_type.days_allowed != old_days:
            year   = date.today().year
            result = sync_balances_for_leave_type(leave_type, year)
            self._sync_result = result
        else:
            self._sync_result = None

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        resp_data = dict(serializer.data)
        if self._sync_result:
            resp_data['balance_sync'] = self._sync_result
        return Response(resp_data)


# ── LEAVE BALANCE ─────────────────────────────────────────────────────────────

class MyLeaveBalanceView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        year = int(request.query_params.get('year', date.today().year))

        # Auto-init if no balances exist yet for this year
        count = LeaveBalance.objects.filter(employee=request.user, year=year).count()
        if count == 0:
            init_balances_for_employee(request.user, year)
        else:
            # Always ensure new leave types that were added after employee
            # onboarding have balance rows created automatically.
            init_balances_for_employee(request.user, year)

        summary = get_leave_balance_summary(request.user, year)
        return Response(summary)


class InitBalanceView(APIView):
    permission_classes = [make_permission('configure_leave')]

    def post(self, request):
        emp_id = request.data.get('employee_id')
        year   = request.data.get('year', date.today().year)

        if not emp_id:
            return Response({'error': 'employee_id required'}, status=400)
        try:
            emp = User.objects.get(pk=emp_id)
        except User.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=404)

        count = init_balances_for_employee(emp, year)
        return Response({'message': f'{count} balances initialised for {emp.username}'})


class SyncLeaveBalancesView(APIView):
    """
    POST /api/leave/sync-balances/
    Body: { "leave_type_id": 3, "year": 2025 }   ← optional year (defaults current)

    Manually trigger a balance sync for a specific leave type across all employees.
    Useful after bulk changes or for backfilling a previous year.
    Admin/HR only.
    """
    permission_classes = [make_permission('configure_leave')]

    def post(self, request):
        lt_id = request.data.get('leave_type_id')
        year  = int(request.data.get('year', date.today().year))

        if not lt_id:
            return Response({'error': 'leave_type_id is required'}, status=400)

        try:
            lt = LeaveType.objects.get(pk=lt_id, tenant_id=get_tenant_id(request))
        except LeaveType.DoesNotExist:
            return Response({'error': 'Leave type not found'}, status=404)

        result = sync_balances_for_leave_type(lt, year)
        return Response({
            'message': f'Balance sync complete for {lt.name} ({year})',
            **result,
        })


class CarryForwardView(APIView):
    """
    POST /api/leave/carry-forward/
    Body: { "year": 2025 }   ← the year ENDING (carry from 2025 to 2026)
    Processes EL/PL carry-forward for all employees.
    Admin/HR only.
    """
    permission_classes = [make_permission('configure_leave')]

    def post(self, request):
        year = int(request.data.get('year', date.today().year - 1))
        result = process_carry_forward(year)
        return Response({
            'message': f"Carry-forward processed: {result['processed']} entries from {result['year_from']} → {result['year_to']}",
            **result,
        })


# ── APPLY LEAVE ───────────────────────────────────────────────────────────────
class ApplyLeaveView(APIView):
    permission_classes = [make_permission('apply_leave')]

    def post(self, request):

        lt_id = request.data.get('leave_type')
        start_str = request.data.get('start_date')
        end_str = request.data.get('end_date')
        session = request.data.get('session', 'full')
        reason = request.data.get('reason', '').strip()

        # ─────────────────────────────────────────────
        # Required fields validation
        # ─────────────────────────────────────────────

        if not all([lt_id, start_str, end_str, reason]):

            return Response({
                'error': (
                    'leave_type, start_date, '
                    'end_date, reason are required'
                )
            }, status=400)

        # ─────────────────────────────────────────────
        # Date parsing
        # ─────────────────────────────────────────────

        try:
            start = date.fromisoformat(start_str)
            end = date.fromisoformat(end_str)

        except ValueError:

            return Response({
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=400)

        # ─────────────────────────────────────────────
        # Date validation
        # ─────────────────────────────────────────────

        if end < start:

            return Response({
                'error': 'end_date must be after start_date'
            }, status=400)

        # ─────────────────────────────────────────────
        # Leave type validation
        # ─────────────────────────────────────────────

        try:

            lt = LeaveType.objects.get(
                pk=lt_id,
                is_active=True,
                tenant_id=get_tenant_id(request),
            )

        except LeaveType.DoesNotExist:

            return Response({
                'error': 'Leave type not found'
            }, status=404)

        blocked_dates = _blocked_leave_dates(start, end)
        if blocked_dates:
            first = blocked_dates[0]
            payload = {
                'blocked_dates': [
                    {
                        'date': str(item['date']),
                        'type': item['type'],
                        'label': item['label'],
                    }
                    for item in blocked_dates
                ],
            }
            if len(blocked_dates) == 1:
                payload['error'] = (
                    f"Cannot apply leave on {first['date']}: "
                    f"this day is {first['label']}."
                )
            else:
                details = ', '.join(
                    f"{item['date']} ({item['label']})"
                    for item in blocked_dates[:5]
                )
                more = f" and {len(blocked_dates) - 5} more" if len(blocked_dates) > 5 else ''
                payload['error'] = (
                    'Cannot apply leave because the selected range includes '
                    f'week off/holiday date(s): {details}{more}.'
                )
            return Response(payload, status=400)

        # ─────────────────────────────────────────────
        # FULLY DYNAMIC NOTICE PERIOD
        # Source = LeaveTypeConfig only
        # ─────────────────────────────────────────────

        effective_notice = int(
            lt.min_notice_days or 0
        )

        if effective_notice > 0:

            notice_days = count_working_days(
                date.today(),
                start
            )

            if notice_days < effective_notice:

                return Response({
                    'error': (
                        f'{lt.name} requires '
                        f'{effective_notice} working day(s) '
                        f'advance notice. '
                        f'Please apply at least '
                        f'{effective_notice} working day(s) '
                        f'before the leave date.'
                    )
                }, status=400)

        # ─────────────────────────────────────────────
        # Working days calculation
        # ─────────────────────────────────────────────

        days = count_working_days(
            start,
            end,
            session
        )

        # ─────────────────────────────────────────────
        # Leave balance check
        # ─────────────────────────────────────────────

        year = date.today().year

        balance = get_or_create_balance(
            request.user,
            lt,
            year
        )

        if balance.remaining < days:

            return Response({
                'error': (
                    f'Insufficient balance. '
                    f'Available: {balance.remaining} day(s), '
                    f'Requested: {days}'
                )
            }, status=400)

        # ─────────────────────────────────────────────
        # Monthly cap check (dynamic)
        # ─────────────────────────────────────────────

        try:

            from attendance.settings_helper import _get

            cl_cap = int(
                _get('cl_monthly_cap', 0)
            )

            if lt.code == 'CL' and cl_cap > 0:

                this_month_used = LeaveRequest.objects.filter(
                    employee=request.user,
                    tenant_id=get_tenant_id(request),
                    leave_type=lt,
                    start_date__year=start.year,
                    start_date__month=start.month,
                    status__in=['approved', 'pending'],
                )

                total_this_month = (
                    sum(float(r.days) for r in this_month_used)
                    + days
                )

                if total_this_month > cl_cap:

                    return Response({
                        'error': (
                            f'CL monthly cap is '
                            f'{cl_cap} day(s). '
                            f'You already used/applied '
                            f'for {total_this_month - days} '
                            f'day(s) this month.'
                        )
                    }, status=400)

        except Exception:
            pass

        # ─────────────────────────────────────────────
        # Overlap check
        # ─────────────────────────────────────────────

        overlap = LeaveRequest.objects.filter(
            employee=request.user,
            tenant_id=get_tenant_id(request),
            status__in=['pending', 'approved'],
            start_date__lte=end,
            end_date__gte=start,
        ).exists()

        if overlap:

            return Response({
                'error': (
                    'You already have a leave request '
                    'overlapping these dates'
                )
            }, status=400)

        # ─────────────────────────────────────────────
        # Create leave request
        # ─────────────────────────────────────────────

        leave = LeaveRequest.objects.create(
            tenant_id=get_tenant_id(request),
            employee=request.user,
            leave_type=lt,
            start_date=start,
            end_date=end,
            days=days,
            session=session,
            reason=reason,
            doc_url=request.data.get(
                'doc_url',
                ''
            ),
        )

        # ─────────────────────────────────────────────
        # Update pending balance
        # ─────────────────────────────────────────────

        balance.pending += days
        balance.save()

        # ─────────────────────────────────────────────
        # Response
        # ─────────────────────────────────────────────

        return Response(
            LeaveRequestSerializer(leave).data,
            status=status.HTTP_201_CREATED
        )
# ── MY LEAVE REQUESTS ─────────────────────────────────────────────────────────

class MyLeaveRequestsView(APIView):
    permission_classes = [make_permission('view_leave')]

    def get(self, request):
        status_filter = request.query_params.get('status')
        qs = LeaveRequest.objects.filter(
            employee=request.user,
            tenant_id=get_tenant_id(request),
        ).select_related('leave_type', 'approved_by')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response(LeaveRequestSerializer(qs, many=True).data)


# ── CANCEL LEAVE ──────────────────────────────────────────────────────────────

class CancelLeaveView(APIView):
    permission_classes = [make_permission('cancel_leave')]

    def post(self, request, pk):
        leave = get_object_or_404(
            LeaveRequest,
            pk=pk,
            employee=request.user,
            tenant_id=get_tenant_id(request),
        )

        if leave.status not in ['pending', 'approved']:
            return Response({'error': f'Cannot cancel a {leave.status} request'}, status=400)

        if leave.status == 'approved' and leave.start_date <= date.today():
            return Response({'error': 'Cannot cancel leave that has already started'}, status=400)

        old_status   = leave.status
        leave.status = 'cancelled'
        leave.save()

        year = leave.start_date.year
        try:
            balance = LeaveBalance.objects.get(
                employee=request.user, leave_type=leave.leave_type, year=year
            )
            if old_status == 'pending':
                balance.pending = max(balance.pending - leave.days, 0)
            elif old_status == 'approved':
                balance.used = max(balance.used - leave.days, 0)
            balance.save()
        except LeaveBalance.DoesNotExist:
            pass

        if old_status == 'approved':
            from datetime import timedelta
            from attendance.models import AttendanceRecord
            cur = leave.start_date
            while cur <= leave.end_date:
                from attendance.settings_helper import is_weekend as _is_wknd
                if not _is_wknd(cur):
                    AttendanceRecord.objects.filter(
                        employee=leave.employee, date=cur,
                    ).update(status='absent', note='Leave cancelled — marked absent')
                cur += timedelta(days=1)

        return Response({'message': 'Leave request cancelled successfully'})


# ── ALL LEAVE REQUESTS (Manager/HR/Admin) ─────────────────────────────────────

class AllLeaveRequestsView(APIView):
    permission_classes = [make_any_permission('view_all_leave', 'approve_leave')]

    def get(self, request):
        status_filter = request.query_params.get('status')
        emp_id        = request.query_params.get('employee')

        qs = LeaveRequest.objects.select_related(
            'employee', 'employee__profile', 'leave_type', 'approved_by'
        ).filter(tenant_id=get_tenant_id(request))

        if status_filter:
            qs = qs.filter(status=status_filter)
        if emp_id:
            qs = qs.filter(employee_id=emp_id)

        return Response(LeaveRequestSerializer(qs, many=True).data)


# ── APPROVE / REJECT ──────────────────────────────────────────────────────────

class LeaveActionView(APIView):
    permission_classes = [make_permission('approve_leave')]

    def post(self, request, pk):
        action = request.data.get('action')
        note   = request.data.get('note', '')

        if action not in ['approve', 'reject']:
            return Response({'error': 'action must be approve or reject'}, status=400)

        leave = get_object_or_404(
            LeaveRequest.objects.select_related('leave_type', 'employee'),
            pk=pk,
            tenant_id=get_tenant_id(request),
        )

        if leave.status != 'pending':
            return Response({'error': f'Request is already {leave.status}'}, status=400)

        if action == 'approve' and _is_comp_off_type(leave.leave_type):
            comp_summary = _comp_off_work_summary(leave.employee, leave)
            if float(leave.days) > comp_summary['available_days']:
                return Response({
                    'error': (
                        f'Insufficient compensatory balance. Available: '
                        f"{comp_summary['available_days']} day(s), requested: {float(leave.days)}"
                    ),
                    'comp_off': comp_summary,
                }, status=400)

        leave.status       = 'approved' if action == 'approve' else 'rejected'
        leave.approved_by  = request.user
        leave.approver_note = note
        leave.save()

        try:
            from notifications.utils import notify_leave_actioned
            notify_leave_actioned(leave, action, request.user)
        except Exception as e:
            print('Leave action notification error:', e)

        year = leave.start_date.year
        try:
            balance = LeaveBalance.objects.get(
                employee=leave.employee,
                leave_type=leave.leave_type,
                year=year,
                tenant_id=get_tenant_id(request),
            )
            balance.pending = max(balance.pending - leave.days, 0)
            if action == 'approve':
                balance.used += leave.days
            balance.save()
        except LeaveBalance.DoesNotExist:
            pass

        if action == 'approve':
            from datetime import timedelta
            from attendance.models import AttendanceRecord
            from attendance.settings_helper import is_weekend as _is_wknd

            is_unpaid  = (not leave.leave_type.is_paid) or (leave.leave_type.code == 'LOP')
            att_status = 'absent' if is_unpaid else 'leave'

            cur = leave.start_date
            while cur <= leave.end_date:
                if not _is_wknd(cur):
                    AttendanceRecord.objects.update_or_create(
                        employee=leave.employee, date=cur,
                        tenant_id=get_tenant_id(request),
                        defaults={'status': att_status, 'note': f'Leave approved: {leave.leave_type.name}'},
                    )
                cur += timedelta(days=1)

        if action == 'reject':
            from datetime import timedelta
            from attendance.models import AttendanceRecord
            from attendance.settings_helper import is_weekend as _is_wknd

            is_half    = leave.session in ('first_half', 'second_half')
            att_status = 'half_day' if is_half else 'absent'

            cur = leave.start_date
            while cur <= leave.end_date:
                if not _is_wknd(cur):
                    AttendanceRecord.objects.update_or_create(
                        employee=leave.employee, date=cur,
                        tenant_id=get_tenant_id(request),
                        defaults={'status': att_status, 'note': f'Leave rejected: {leave.leave_type.name}'},
                    )
                cur += timedelta(days=1)

        return Response({
            'message': f'Leave {leave.status}',
            'data': LeaveRequestSerializer(leave).data,
        })


# ── PRIOR USAGE CHECK ─────────────────────────────────────────────────────────

class LeavePriorUsageView(APIView):
    permission_classes = [make_permission('approve_leave')]

    def get(self, request, pk):
        leave = get_object_or_404(
            LeaveRequest.objects.select_related('employee', 'leave_type'),
            pk=pk,
            tenant_id=get_tenant_id(request),
        )
        month      = leave.start_date.month
        year       = leave.start_date.year
        employee   = leave.employee
        leave_type = leave.leave_type

        prior_qs = LeaveRequest.objects.filter(
            employee=employee, leave_type=leave_type,
            tenant_id=get_tenant_id(request),
            start_date__year=year, start_date__month=month,
            status__in=['approved', 'pending'],
        ).exclude(pk=pk).order_by('start_date')

        prior_approved = [r for r in prior_qs if r.status == 'approved']
        prior_pending  = [r for r in prior_qs if r.status == 'pending']

        def fmt(r):
            return {
                'id': r.id, 'start_date': str(r.start_date),
                'end_date': str(r.end_date), 'days': float(r.days),
                'status': r.status, 'applied_at': r.applied_at.strftime('%d %b %Y'),
            }

        total_prior_days = sum(float(r.days) for r in prior_qs)

        try:
            balance = LeaveBalance.objects.get(employee=employee, leave_type=leave_type, year=year)
            annual_balance = {
                'total': float(balance.total), 'used': float(balance.used),
                'pending': float(balance.pending), 'remaining': float(balance.remaining),
                'carried': float(balance.carried or 0),
            }
        except LeaveBalance.DoesNotExist:
            annual_balance = None

        import calendar
        comp_summary = _comp_off_work_summary(employee, leave) if _is_comp_off_type(leave_type) else None
        return Response({
            'employee_name':    employee.get_full_name() or employee.username,
            'leave_type':       leave_type.name,
            'leave_code':       leave_type.code,
            'month':            f'{calendar.month_name[month]} {year}',
            'requested_days':   float(leave.days),
            'prior_approved':   [fmt(r) for r in prior_approved],
            'prior_pending':    [fmt(r) for r in prior_pending],
            'total_prior_days': total_prior_days,
            'annual_balance':   annual_balance,
            'has_prior':        total_prior_days > 0,
            'is_compensatory':   comp_summary is not None,
            'comp_off':         comp_summary,
        })
# ── LEAVE POLICY SETTINGS SYNC ────────────────────────────────────────────────

class LeavePolicySettingsView(APIView):
    """
    GET  /api/leave/policy-settings/
        Returns per-leave-type effective settings (merged: system settings win,
        LeaveType fields as fallback). Used by LeaveTypeConfig editor to show
        what system settings currently say for each leave type.

    POST /api/leave/policy-settings/
        Body: { "leave_type_id": 1, "fields": { "min_notice_days": 3, "days_allowed": 15, ... } }
        Saves changes BOTH to LeaveType record AND to SystemSetting keys so
        both places stay in sync.  Admin/HR only.
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticatedUser()]
        return [make_permission('configure_leave')()]

    def get(self, request):
        from attendance.settings_helper import (
            get_leave_advance_notice_days,
            get_leave_days_allowed,
            get_leave_is_paid,
            get_leave_carry_forward,
        )
        leave_types = LeaveType.objects.filter(is_active=True, tenant_id=get_tenant_id(request))
        result = []
        for lt in leave_types:
            code = lt.code

            # days_allowed: system setting wins if set
            sys_days = get_leave_days_allowed(code)
            eff_days = sys_days if sys_days >= 0 else lt.days_allowed

            # min_notice_days: system setting wins if > 0
            sys_notice = get_leave_advance_notice_days(code)
            eff_notice = sys_notice if sys_notice > 0 else lt.min_notice_days

            # is_paid: system setting wins if set (0 or 1), else use model
            sys_paid = get_leave_is_paid(code)
            eff_paid = (sys_paid == 1) if sys_paid >= 0 else lt.is_paid

            # carry_forward: system setting wins if set
            # Fully dynamic carry forward from LeaveTypeConfig only

            eff_cf = bool(
    lt.carry_forward
)
            result.append({
                'id':                  lt.id,
                'name':                lt.name,
                'code':                code,
                'applicable_to':       lt.applicable_to,
                'description':         lt.description,
                'requires_document':   lt.requires_document,
                'max_carry_forward':   lt.max_carry_forward,

                # effective values (system setting merged with model)
                'days_allowed':        eff_days,
                'min_notice_days':     eff_notice,
                'is_paid':             eff_paid,
                'carry_forward':       eff_cf,

                # where each value comes from
                'days_allowed_source':    'system_settings' if sys_days >= 0 else 'leave_type',
                'notice_days_source':     'system_settings' if sys_notice > 0 else 'leave_type',
                'is_paid_source':         'system_settings' if sys_paid >= 0 else 'leave_type',
                'carry_forward_source':   'leave_type',
            })
        return Response(result)

    def post(self, request):
        """
        Sync a leave type's editable fields to BOTH LeaveType model AND SystemSetting.
        This is the single save point — no separate saves needed in settings page.
        """
        from notifications.models import SystemSetting

        lt_id  = request.data.get('leave_type_id')
        fields = request.data.get('fields', {})

        if not lt_id:
            return Response({'error': 'leave_type_id required'}, status=400)

        try:
            lt = LeaveType.objects.get(pk=lt_id, tenant_id=get_tenant_id(request))
        except LeaveType.DoesNotExist:
            return Response({'error': 'Leave type not found'}, status=404)

        code = lt.code.lower()
        updated_model_fields = []
        updated_settings = []

        # ── days_allowed ─────────────────────────────────────────────────────
        if 'days_allowed' in fields:
            val = int(fields['days_allowed'])
            lt.days_allowed = val
            updated_model_fields.append('days_allowed')
            # sync to system setting
            key = f'{code}_days_per_year'
            obj, _ = SystemSetting.objects.get_or_create(
                tenant_id=get_tenant_id(request),
                key=key,
                defaults={
                    'value': str(val), 'value_type': 'integer',
                    'label': f'{lt.name} — Days/Year', 'category': 'leave',
                    'description': f'Annual {lt.name} allocation.',
                }
            )
            obj.value = str(val)
            obj.save(update_fields=['value'])
            updated_settings.append(key)

        # ── min_notice_days ───────────────────────────────────────────────────
        if 'min_notice_days' in fields:
            val = int(fields['min_notice_days'])
            lt.min_notice_days = val
            updated_model_fields.append('min_notice_days')
            key = f'{code}_advance_notice_days'
            obj, _ = SystemSetting.objects.get_or_create(
                tenant_id=get_tenant_id(request),
                key=key,
                defaults={
                    'value': str(val), 'value_type': 'integer',
                    'label': f'{lt.name} Advance Notice (Days)', 'category': 'leave',
                    'description': f'Min working days notice required for {lt.name}.',
                }
            )
            obj.value = str(val)
            obj.save(update_fields=['value'])
            updated_settings.append(key)

        # ── is_paid ───────────────────────────────────────────────────────────
        if 'is_paid' in fields:
            val = bool(fields['is_paid'])
            lt.is_paid = val
            updated_model_fields.append('is_paid')
            key = f'{code}_is_paid'
            obj, _ = SystemSetting.objects.get_or_create(
                tenant_id=get_tenant_id(request),
                key=key,
                defaults={
                    'value': str(val).lower(), 'value_type': 'boolean',
                    'label': f'{lt.name} — Paid Leave', 'category': 'leave',
                    'description': f'Whether {lt.name} is paid.',
                }
            )
            obj.value = str(val).lower()
            obj.save(update_fields=['value'])
            updated_settings.append(key)

        # ── carry_forward ─────────────────────────────────────────────────────
        if 'carry_forward' in fields:
            val = bool(fields['carry_forward'])
            lt.carry_forward = val
            updated_model_fields.append('carry_forward')
            key = f'{code}_carry_forward'
            obj, _ = SystemSetting.objects.get_or_create(
                tenant_id=get_tenant_id(request),
                key=key,
                defaults={
                    'value': str(val).lower(), 'value_type': 'boolean',
                    'label': f'{lt.name} — Carry Forward', 'category': 'leave',
                    'description': f'Whether unused {lt.name} carries to next year.',
                }
            )
            obj.value = str(val).lower()
            obj.save(update_fields=['value'])
            updated_settings.append(key)

        # ── other direct model fields ─────────────────────────────────────────
        for field in ('name', 'applicable_to', 'description',
                      'requires_document', 'max_carry_forward'):
            if field in fields:
                setattr(lt, field, fields[field])
                updated_model_fields.append(field)

        if updated_model_fields:
            lt.save(update_fields=list(set(updated_model_fields)))

        balance_sync = None
        if 'days_allowed' in updated_model_fields:
            balance_sync = sync_balances_for_leave_type(lt, date.today().year)

        return Response({
            'message':          'Saved to both LeaveType and SystemSettings',
            'leave_type_id':    lt.id,
            'updated_fields':   list(set(updated_model_fields)),
            'synced_settings':  updated_settings,
            'balance_sync':     balance_sync,
        })
    

class DeleteLeaveTypeView(APIView):

    permission_classes = [
        make_permission('configure_leave')
    ]

    def delete(self, request, pk):

        try:
            lt = LeaveType.objects.get(pk=pk, tenant_id=get_tenant_id(request))

        except LeaveType.DoesNotExist:

            return Response({
                'error': 'Leave type not found'
            }, status=404)

        lt.delete()

        return Response({
            'message': 'Leave type deleted successfully'
        })
