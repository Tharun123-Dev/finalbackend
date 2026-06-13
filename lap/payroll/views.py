# payroll/views.py
import calendar
from datetime import date, datetime
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.shortcuts import get_object_or_404
from django.db import transaction

from utils.permissions import make_permission, IsAuthenticatedUser
from accounts.tenant_utils import get_tenant_id
from accounts.models import User
from .models import SalaryStructure, PayrollRun, PayrollEntry, PayrollAdjustment
from .serializers import (
    SalaryStructureSerializer, PayrollRunSerializer,
    PayrollEntrySerializer, AdjustmentSerializer
)
from .engine import process_payroll_run
from attendance.settings_helper import (
    get_basic_salary_percent, get_hra_metro_percent, get_hra_nonmetro_percent,
    get_da_percent, get_pf_employee_percent, get_pf_employer_percent,
    get_esi_employee_percent, get_esi_employer_percent, get_esi_threshold,
    get_payroll_lock_day, get_tds_flat_contract, get_pt_flat_amount,
    get_pt_threshold_salary, get_pt_below_threshold_amount,
    get_pt_above_threshold_amount, calculate_professional_tax,
    get_overtime_multiplier,
    get_company_name, get_currency, get_fiscal_year_start_month, get_probation_months,
    get_default_transport, get_default_medical, get_default_other_allowance,
    get_default_pt, get_working_days_per_month,
)


def _get_general(key, default='', tenant_id='default'):
    """Read a general system setting directly."""
    try:
        from notifications.models import SystemSetting
        s = SystemSetting.objects.filter(tenant_id=tenant_id, key=key).first()
        if s:
            return s.get_value()
    except Exception:
        pass
    return default


# ── PAYROLL SETTINGS DEFAULTS (for salary config auto-fill) ───────────────────

class PayrollSettingsDefaultsView(APIView):
    """
    Returns all current payroll system setting values.
    Frontend SalaryConfig calls this to auto-fill the form when CTC is entered.
    Changing any setting in System Settings immediately reflects here.
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        return Response({
            'basic_percent':            float(get_basic_salary_percent()),
            'hra_percent_metro':        float(get_hra_metro_percent()),
            'hra_percent_nonmetro':     float(get_hra_nonmetro_percent()),
            'da_percent':               float(get_da_percent()),
            'pf_employee_percent':      float(get_pf_employee_percent()),
            'pf_employer_percent':      float(get_pf_employer_percent()),
            'esi_employee_percent':     float(get_esi_employee_percent()),
            'esi_employer_percent':     float(get_esi_employer_percent()),
            'esi_threshold':            float(get_esi_threshold()),
            'payroll_lock_day':         get_payroll_lock_day(),
            'tds_flat_contract':        float(get_tds_flat_contract()),
            'overtime_multiplier':      float(get_overtime_multiplier()),
            'pt_flat_amount':            float(get_pt_flat_amount()),
            'pt_threshold_salary':       float(get_pt_threshold_salary()),
            'pt_below_threshold_amount': float(get_pt_below_threshold_amount()),
            'pt_above_threshold_amount': float(get_pt_above_threshold_amount()),
            # Fixed allowance defaults — fully from System Settings
            'default_transport':        float(get_default_transport()),
            'default_medical':          float(get_default_medical()),
            'default_other_allowance':  float(get_default_other_allowance()),
            'default_pt':               float(get_default_pt()),
            'working_days_per_month':   get_working_days_per_month(),
            # General settings
            'company_name':             get_company_name(),
            'company_logo_url':         str(_get_general('company_logo_url', '', get_tenant_id(request))),
            'currency':                 get_currency(),
            'fiscal_year_start_month':  float(get_fiscal_year_start_month()),
            'probation_period_months':  get_probation_months(),
        })


# ── SALARY STRUCTURE ──────────────────────────────────────────────────────────

def _serialize_structure(structure):
    """
    Serialize a SalaryStructure using the STORED percentages exactly as saved.
    The list and MySalaryView show what was actually created — not overridden
    by whatever the current system settings happen to be.
    System settings are only used as FORM DEFAULTS when opening Assign Salary.
    """
    ctc       = float(structure.ctc)
    monthly   = ctc / 12

    # Use STORED percentages — exactly what was saved
    basic_pct = float(structure.basic_percent) / 100
    hra_pct   = float(structure.hra_percent)   / 100
    da_pct    = float(structure.da_percent)    / 100
    pf_pct    = float(structure.pf_percent)    / 100
    esi_pct   = float(structure.esi_percent)   / 100

    transport = float(structure.transport)
    medical   = float(structure.medical)
    other     = float(structure.other_allowance)
    basic     = round(monthly * basic_pct, 2)
    hra       = round(basic   * hra_pct, 2)
    da        = round(basic   * da_pct, 2)
    special   = round(max(monthly - basic - hra - da - transport - medical - other, 0), 2)
    gross     = round(basic + hra + da + special + transport + medical + other, 2)
    # PT: always show live gross-based system settings value.
    pt        = float(calculate_professional_tax(gross))

    # Always use 21000 as ESI threshold minimum — system setting may be misconfigured
    raw_threshold = float(get_esi_threshold())
    esi_threshold = raw_threshold if raw_threshold >= 1000 else 21000
    pf_emp    = round(basic * pf_pct, 2)
    esi_exempt = gross > esi_threshold
    esi_emp   = 0.0 if esi_exempt else round(gross * esi_pct, 2)
    total_ded = round(pf_emp + esi_emp + pt, 2)
    net_pay   = round(gross - total_ded, 2)

    pf_er     = round(basic * float(get_pf_employer_percent())  / 100, 2)
    esi_er    = 0.0 if esi_exempt else round(gross * float(get_esi_employer_percent()) / 100, 2)
    employer_contrib = round(pf_er + esi_er, 2)
    monthly_company_cost = round(gross + employer_contrib, 2)
    ctc_difference = round(monthly - monthly_company_cost, 2)

    try:
        emp_name = structure.employee.get_full_name().strip() or structure.employee.username
    except Exception:
        emp_name = structure.employee.username

    try:
        emp_code = structure.employee.profile.emp_code
    except Exception:
        emp_code = ''

    return {
        'id':               structure.id,
        'employee':         structure.employee_id,
        'employee_name':    emp_name,
        'employee_email':   structure.employee.email,
        'emp_code':         emp_code,
        'effective_date':   str(structure.effective_date),
        'ctc':              ctc,
        'monthly_ctc':      round(monthly, 2),
        # stored percentages (exactly what was saved at creation)
        'basic_percent':    float(structure.basic_percent),
        'hra_percent':      float(structure.hra_percent),
        'da_percent':       float(structure.da_percent),
        'pf_percent':       float(structure.pf_percent),
        'esi_percent':      float(structure.esi_percent),
        # fixed allowances (stored)
        'transport':        transport,
        'medical':          medical,
        'other_allowance':  other,
        'pt':               pt,
        # computed values
        'basic':            basic,
        'hra':              hra,
        'da':               da,
        'special_allowance': special,
        'gross':            gross,
        'pf_employee':      pf_emp,
        'esi_employee':     esi_emp,
        'esi_threshold':    esi_threshold,
        'esi_exempt':       esi_exempt,
        'total_deductions': total_ded,
        'net_pay':          net_pay,
        'earnings_breakdown': {
            'basic': basic,
            'hra': hra,
            'da': da,
            'special_allowance': special,
            'transport': transport,
            'medical': medical,
            'other_allowance': other,
            'gross': gross,
        },
        'deductions_breakdown': {
            'pf_employee': pf_emp,
            'esi_employee': esi_emp,
            'pt': pt,
            'tds': 0,
            'lop_deduction': 0,
            'total_deductions': total_ded,
            'net_pay': net_pay,
        },
        'calculation_summary': {
            'monthly_ctc': round(monthly, 2),
            'monthly_gross': gross,
            'employee_deductions': total_ded,
            'net_pay': net_pay,
            'employer_pf': pf_er,
            'employer_esi': esi_er,
            'employer_contribution': employer_contrib,
            'monthly_company_cost': monthly_company_cost,
            'ctc_difference': ctc_difference,
            'esi_exempt': esi_exempt,
        },
        # employer contributions
        'pf_employer':      pf_er,
        'esi_employer':     esi_er,
        'is_active':        structure.is_active,
        'created_at':       str(structure.created_at),
    }


class SalaryStructureListView(APIView):
    permission_classes = [make_permission('view_salary')]

    def get(self, request):
        emp_id = request.query_params.get('employee')
        qs = SalaryStructure.objects.select_related(
            'employee', 'employee__profile'
        ).filter(is_active=True, tenant_id=get_tenant_id(request))

        if emp_id:
            qs = qs.filter(employee_id=emp_id)

        # Serialize using STORED percentages — shows exactly what was created
        data = [_serialize_structure(s) for s in qs]
        return Response(data)


def _base_payroll_role(role_value):
    value = str(role_value or '').lower()
    if 'super' in value and 'admin' in value:
        return 'superadmin'
    if 'admin' in value:
        return 'admin'
    if value.startswith('hr') or 'human_resource' in value:
        return 'hr'
    if 'manager' in value:
        return 'manager'
    if 'counsel' in value:
        return 'counselor'
    return 'employee'


def _resolve_salary_employee(request):
    tenant_id = get_tenant_id(request)
    emp_id = request.data.get('employee')
    java_user_id = request.data.get('java_user_id') or emp_id
    email = str(
        request.data.get('employee_email')
        or request.data.get('email')
        or ''
    ).strip()

    user = None
    if email:
        user = User.objects.filter(email=email, tenant_id=tenant_id).first()

    if user is None and emp_id:
        try:
            user = User.objects.get(pk=emp_id, tenant_id=tenant_id)
        except (User.DoesNotExist, ValueError, TypeError):
            user = None

    if user is not None:
        return user

    if not email and not java_user_id:
        return None

    username = str(request.data.get('employee_username') or email or f'java-user-{java_user_id}@lap.local').strip()
    email = email or username
    first_name = str(request.data.get('employee_first_name') or '').strip()
    last_name = str(request.data.get('employee_last_name') or '').strip()
    employee_type = str(request.data.get('employee_type') or 'regular').lower()
    if employee_type not in {'regular', 'contract', 'parttime', 'intern'}:
        employee_type = 'regular'

    base_username = username
    suffix = 1
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f'{base_username}-{suffix}'

    user = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=_base_payroll_role(request.data.get('employee_role') or request.data.get('roleName')),
        employee_type=employee_type,
        tenant_id=tenant_id,
        is_active=True,
    )
    user.set_unusable_password()
    user.save()
    return user


class CreateSalaryStructureView(APIView):
    permission_classes = [make_permission('configure_salary')]

    def post(self, request):
        emp = _resolve_salary_employee(request)
        if not emp:
            return Response({'error': 'Employee not found'}, status=404)

        # Use system settings as defaults if not provided — zero hardcodes
        data = {
            'employee':        emp.id,
            'effective_date':  request.data.get('effective_date'),
            'ctc':             request.data.get('ctc', 0),
            'basic_percent':   request.data.get('basic_percent',   float(get_basic_salary_percent())),
            'hra_percent':     request.data.get('hra_percent',     float(get_hra_metro_percent())),
            'da_percent':      request.data.get('da_percent',      float(get_da_percent())),
            'pf_percent':      request.data.get('pf_percent',      float(get_pf_employee_percent())),
            'esi_percent':     request.data.get('esi_percent',     float(get_esi_employee_percent())),
            'transport':       request.data.get('transport',       float(get_default_transport())),
            'medical':         request.data.get('medical',         float(get_default_medical())),
            'other_allowance': request.data.get('other_allowance', float(get_default_other_allowance())),
            'pt':              request.data.get('pt',              float(get_default_pt())),
        }

        # CTC validation
        try:
            ctc       = Decimal(str(data.get('ctc', 0)))
            basic_pct = Decimal(str(data.get('basic_percent', float(get_basic_salary_percent())))) / Decimal('100')
            hra_pct   = Decimal(str(data.get('hra_percent',   float(get_hra_metro_percent()))))    / Decimal('100')
            da_pct    = Decimal(str(data.get('da_percent',    float(get_da_percent()))))           / Decimal('100')
            tr        = Decimal(str(data.get('transport', 0)))
            med       = Decimal(str(data.get('medical', 0)))
            oth       = Decimal(str(data.get('other_allowance', 0)))

            monthly_ctc = ctc / Decimal('12')
            basic  = monthly_ctc * basic_pct
            hra    = basic * hra_pct
            da     = basic * da_pct
            pf_er  = basic * get_pf_employer_percent() / Decimal('100')
            esi_er = (basic + hra + da + tr + med + oth) * get_esi_employer_percent() / Decimal('100')

            gross_components = basic + hra + da + tr + med + oth
            preview_gross = monthly_ctc
            data['pt'] = float(calculate_professional_tax(preview_gross))
            total_ctc_month  = gross_components + pf_er + esi_er
            ctc_diff = abs(ctc / Decimal('12') - total_ctc_month)
            ctc_warning = None
            if ctc > 0 and ctc_diff > Decimal('500'):
                ctc_warning = (
                    f"CTC ₹{ctc} — Monthly gross components ₹{round(total_ctc_month, 2)}. "
                    f"Difference: ₹{round(ctc_diff, 2)} (employer contributions included)"
                )
        except Exception:
            ctc_warning = None

        # Deactivate old structure
        SalaryStructure.objects.filter(
            employee=emp,
            is_active=True,
            tenant_id=get_tenant_id(request),
        ).update(is_active=False)

        serializer = SalaryStructureSerializer(data=data)
        if serializer.is_valid():
            obj = serializer.save(created_by=request.user, tenant_id=get_tenant_id(request))
            resp = _serialize_structure(obj)
            if ctc_warning:
                resp['ctc_warning'] = ctc_warning
            return Response(resp, status=201)

        return Response(serializer.errors, status=400)


class UpdateSalaryStructureView(APIView):
    permission_classes = [make_permission('configure_salary')]

    def patch(self, request, pk):
        structure = get_object_or_404(SalaryStructure, pk=pk, tenant_id=get_tenant_id(request))
        serializer = SalaryStructureSerializer(
            structure, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class MySalaryStructureView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        structure = SalaryStructure.objects.filter(
            employee=request.user,
            is_active=True,
            tenant_id=get_tenant_id(request),
        ).order_by('-effective_date').first()

        if not structure:
            return Response(None, status=200)

        # Use stored percentages — show exactly what was assigned
        return Response(_serialize_structure(structure))


# ── PAYROLL RUNS ──────────────────────────────────────────────────────────────

def _run_period_from_request(request, month, year):
    last_day = calendar.monthrange(year, month)[1]
    start_raw = request.data.get('period_start') or request.data.get('start_date')
    end_raw = request.data.get('period_end') or request.data.get('end_date')

    if start_raw or end_raw:
        if not start_raw or not end_raw:
            raise ValueError('Both period_start and period_end are required for split payroll')
        period_start = datetime.strptime(str(start_raw), '%Y-%m-%d').date()
        period_end = datetime.strptime(str(end_raw), '%Y-%m-%d').date()
    else:
        period_start = date(year, month, 1)
        period_end = date(year, month, last_day)

    if period_start.year != year or period_start.month != month or period_end.year != year or period_end.month != month:
        raise ValueError('Payroll period dates must be inside the selected month/year')
    if period_start > period_end:
        raise ValueError('period_start cannot be after period_end')
    return period_start, period_end


def _overlapping_run(month, year, period_start, period_end, tenant_id='default'):
    return PayrollRun.objects.filter(
        tenant_id=tenant_id,
        month=month,
        year=year,
        period_start__lte=period_end,
        period_end__gte=period_start,
    ).first()


def _payroll_employee_options(run):
    processed_ids = set(run.entries.values_list('employee_id', flat=True))
    as_of = run.period_end
    employees = User.objects.filter(is_active=True, tenant_id=run.tenant_id).select_related('profile').order_by(
        'first_name', 'last_name', 'username'
    )
    data = []
    for emp in employees:
        structure = SalaryStructure.objects.filter(
            employee=emp, is_active=True, effective_date__lte=as_of,
        ).order_by('-effective_date').first()
        if not structure:
            structure = SalaryStructure.objects.filter(
                employee=emp, is_active=True,
            ).order_by('-effective_date').first()
        try:
            emp_code = emp.profile.emp_code
        except Exception:
            emp_code = ''
        data.append({
            'id': emp.id,
            'name': emp.get_full_name() or emp.username,
            'emp_code': emp_code,
            'has_salary': bool(structure),
            'processed': emp.id in processed_ids,
        })
    return data


class PayrollRunListView(generics.ListAPIView):
    serializer_class   = PayrollRunSerializer
    permission_classes = [make_permission('view_payroll')]

    def get_queryset(self):
        return PayrollRun.objects.filter(tenant_id=get_tenant_id(self.request))


class CreatePayrollRunView(APIView):
    permission_classes = [make_permission('process_payroll')]

    def post(self, request):
        month = int(request.data.get('month', date.today().month))
        year  = int(request.data.get('year',  date.today().year))
        notes = request.data.get('notes', '')
        try:
            period_start, period_end = _run_period_from_request(request, month, year)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=400)

        overlap = _overlapping_run(month, year, period_start, period_end, get_tenant_id(request))
        if overlap:
            if overlap.period_start == period_start and overlap.period_end == period_end:
                data = PayrollRunSerializer(overlap).data
                data['existing'] = True
                return Response(data, status=200)
            return Response(
                {
                    'error': (
                        f'Payroll already exists for {overlap.period_label} '
                        f'({overlap.period_start} to {overlap.period_end}). '
                        'Choose only remaining dates for a split payroll.'
                    )
                },
                status=400
            )

        run = PayrollRun.objects.create(
            tenant_id    = get_tenant_id(request),
            month        = month,
            year         = year,
            period_start = period_start,
            period_end   = period_end,
            notes        = notes,
            processed_by = request.user,
            status       = 'draft',
        )
        return Response(PayrollRunSerializer(run).data, status=201)


class ProcessPayrollRunView(APIView):
    """Calculate payroll for all employees in the run."""
    permission_classes = [make_permission('process_payroll')]

    def post(self, request, pk):
        run = get_object_or_404(PayrollRun, pk=pk, tenant_id=get_tenant_id(request))

        if run.status == 'locked':
            return Response({'error': 'Payroll is locked and cannot be reprocessed'}, status=400)

        # Enforce payroll lock day: can only process if today >= lock_day for that month
        today     = date.today()
        lock_day  = get_payroll_lock_day()
        run_year  = run.year
        run_month = run.month

        # Allow processing for past months freely; for current month enforce lock day
        is_current_month = (today.year == run_year and today.month == run_month)
        if is_current_month and today.day < lock_day:
            return Response({
                'error': (
                    f'Payroll for {run_month}/{run_year} can only be processed '
                    f'on or after day {lock_day} of the month. '
                    f'Today is {today.day}. Change payroll_lock_day in System Settings if needed.'
                )
            }, status=400)

        with transaction.atomic():
            employee_id = request.data.get('employee') or request.data.get('employee_id')
            employee_ids = [employee_id] if employee_id else None
            if employee_id and PayrollEntry.objects.filter(payroll_run=run, employee_id=employee_id, tenant_id=get_tenant_id(request)).exists():
                return Response({'error': 'Payroll already processed for this employee in this period'}, status=400)
            if not employee_id:
                PayrollEntry.objects.filter(
                    payroll_run=run,
                    tenant_id=get_tenant_id(request),
                ).delete()

            created, skipped = process_payroll_run(run, employee_ids=employee_ids)
            if not created and employee_id and not skipped:
                return Response({'error': 'No available employee found to process'}, status=400)
            if not created and employee_id and skipped:
                return Response({'error': 'Selected employee has no active salary structure'}, status=400)
            run.status       = 'processed'
            run.processed_by = request.user
            run.save()

        return Response({
            'message': f'Payroll processed for {run.month}/{run.year} ({run.period_label})',
            'created': len(created),
            'skipped': skipped,
            'run':     PayrollRunSerializer(run).data,
        })


class ApprovePayrollRunView(APIView):
    permission_classes = [make_permission('approve_payroll')]

    def post(self, request, pk):
        run = get_object_or_404(PayrollRun, pk=pk, tenant_id=get_tenant_id(request))

        if run.status != 'processed':
            return Response(
                {'error': f'Payroll must be in processed state to approve. Current: {run.status}'},
                status=400
            )

        run.status      = 'locked'
        run.approved_by = request.user
        run.locked_at   = datetime.now()
        run.save()

        return Response({
            'message': f'Payroll {run.month}/{run.year} ({run.period_label}) approved and locked',
            'run':     PayrollRunSerializer(run).data,
        })


class PayrollRunDetailView(APIView):
    permission_classes = [make_permission('view_payroll')]

    def get(self, request, pk):
        run     = get_object_or_404(PayrollRun, pk=pk, tenant_id=get_tenant_id(request))
        entries = PayrollEntry.objects.filter(
            payroll_run=run,
            tenant_id=get_tenant_id(request),
        ).select_related('employee', 'employee__profile', 'salary_structure')

        return Response({
            'run':     PayrollRunSerializer(run).data,
            'entries': PayrollEntrySerializer(entries, many=True).data,
            'available_employees': _payroll_employee_options(run),
        })


# ── PAYROLL ENTRY ─────────────────────────────────────────────────────────────

class UpdatePayrollEntryView(APIView):
    permission_classes = [make_permission('process_payroll')]

    def patch(self, request, pk):
        entry = get_object_or_404(PayrollEntry, pk=pk, tenant_id=get_tenant_id(request))

        if entry.payroll_run.status == 'locked':
            return Response({'error': 'Cannot edit a locked payroll'}, status=400)

        editable = ['basic', 'hra', 'da', 'special_allowance', 'transport',
                    'medical', 'other_allowance', 'tds', 'lop_days', 'lop_deduction']

        for field in editable:
            if field in request.data:
                setattr(entry, field, request.data[field])

        entry.gross = (
            entry.basic + entry.hra + entry.da +
            entry.special_allowance + entry.transport +
            entry.medical + entry.other_allowance + entry.ot_pay
        )
        ratio = (
            Decimal(str(entry.present_days)) / Decimal(str(entry.working_days))
            if entry.working_days else Decimal('0')
        )
        effective_gross = max(entry.gross - entry.lop_deduction, Decimal('0'))
        entry.pt = (calculate_professional_tax(effective_gross) * ratio).quantize(Decimal('0.01'))
        entry.total_deductions = (
            entry.pf_employee + entry.esi_employee +
            entry.pt + entry.tds + entry.lop_deduction
        )
        entry.net_pay = max(entry.gross - entry.total_deductions, Decimal('0'))
        entry.save()

        return Response(PayrollEntrySerializer(entry).data)


# ── ADJUSTMENTS ───────────────────────────────────────────────────────────────

class AddAdjustmentView(APIView):
    permission_classes = [make_permission('process_payroll')]

    def post(self, request, entry_pk):
        entry = get_object_or_404(PayrollEntry, pk=entry_pk, tenant_id=get_tenant_id(request))

        if entry.payroll_run.status == 'locked':
            return Response({'error': 'Cannot adjust a locked payroll'}, status=400)

        adj_type = request.data.get('type')
        amount   = Decimal(str(request.data.get('amount', 0)))
        reason   = request.data.get('reason', '')

        if adj_type not in ['bonus', 'reimbursement', 'deduction', 'arrear']:
            return Response({'error': 'Invalid adjustment type'}, status=400)

        adj = PayrollAdjustment.objects.create(
            tenant_id      = get_tenant_id(request),
            payroll_entry = entry,
            type          = adj_type,
            amount        = amount,
            reason        = reason,
            added_by      = request.user,
        )

        if adj_type in ['bonus', 'reimbursement', 'arrear']:
            entry.net_pay += amount
            entry.gross   += amount
        else:
            entry.net_pay          = max(entry.net_pay - amount, Decimal('0'))
            entry.total_deductions += amount
        entry.save()

        return Response(AdjustmentSerializer(adj).data, status=201)


# ── MY PAYSLIP ────────────────────────────────────────────────────────────────

class MyPayslipListView(APIView):
    permission_classes = [make_permission('view_payslip')]

    def get(self, request):
        entries = PayrollEntry.objects.filter(
            employee=request.user,
            tenant_id=get_tenant_id(request),
            payroll_run__status='locked',
        ).select_related('payroll_run', 'salary_structure').order_by(
            '-payroll_run__year', '-payroll_run__month'
        )
        return Response(PayrollEntrySerializer(entries, many=True).data)


class MyPayslipDetailView(APIView):
    permission_classes = [make_permission('view_payslip')]

    def get(self, request, month, year):
        entry = PayrollEntry.objects.filter(
            employee=request.user,
            tenant_id=get_tenant_id(request),
            payroll_run__month=month,
            payroll_run__year=year,
            payroll_run__status='locked',
        ).select_related('payroll_run', 'salary_structure', 'employee__profile').first()

        if not entry:
            return Response({'detail': 'Payslip not found'}, status=404)

        return Response(PayrollEntrySerializer(entry).data)


# ── PAYROLL REGISTER (Admin/HR) ───────────────────────────────────────────────

class PayrollRegisterView(APIView):
    permission_classes = [make_permission('view_payroll')]

    def get(self, request, pk):
        run = get_object_or_404(PayrollRun, pk=pk, tenant_id=get_tenant_id(request))
        entries = PayrollEntry.objects.filter(
            payroll_run=run,
            tenant_id=get_tenant_id(request),
        ).select_related(
            'employee', 'employee__profile', 'employee__profile__department'
        )

        data = []
        for e in entries:
            try:
                bank_account = e.employee.profile.bank_account
                ifsc         = e.employee.profile.ifsc_code
                emp_code     = e.employee.profile.emp_code
            except Exception:
                bank_account = ''
                ifsc         = ''
                emp_code     = ''

            data.append({
                'emp_code':         emp_code,
                'name':             e.employee.get_full_name(),
                'bank_account':     bank_account,
                'ifsc':             ifsc,
                'net_pay':          float(e.net_pay),
                'gross':            float(e.gross),
                'total_deductions': float(e.total_deductions),
                'lop_days':         float(e.lop_days),
                'present_days':     float(e.present_days),
                'extra_work_days':  float(e.extra_work_days),
                'extra_work_pay':   float(e.extra_work_pay),
                'comp_off_days':    float(e.comp_off_days),
            })

        summary = {
            'total_gross':    float(sum(e.gross for e in entries)),
            'total_net':      float(sum(e.net_pay for e in entries)),
            'total_pf':       float(sum(e.pf_employee for e in entries)),
            'total_esi':      float(sum(e.esi_employee for e in entries)),
            'total_tds':      float(sum(e.tds for e in entries)),
            'total_lop':      float(sum(e.lop_deduction for e in entries)),
            'total_extra_work_pay': float(sum(e.extra_work_pay for e in entries)),
            'employee_count': entries.count(),
        }

        return Response({
            'run':     PayrollRunSerializer(run).data,
            'summary': summary,
            'entries': data,
        })


# ── DEDUCTION HISTORY — MY OWN ────────────────────────────────────────────────

class MyDeductionHistoryView(APIView):
    permission_classes = [make_permission('view_payslip')]

    def get(self, request):
        year = request.query_params.get('year', date.today().year)

        entries = PayrollEntry.objects.filter(
            employee            = request.user,
            payroll_run__status = 'locked',
            payroll_run__year   = year,
        ).select_related('payroll_run').order_by(
            'payroll_run__year', 'payroll_run__month'
        )

        history = []
        for e in entries:
            run = e.payroll_run
            history.append({
                'month':            run.month,
                'year':             run.year,
                'gross':            float(e.gross),
                'present_days':     float(e.present_days),
                'working_days':     int(e.working_days),
                'lop_days':         float(e.lop_days),
                'ot_hours':         float(e.ot_hours),
                'ot_pay':           float(e.ot_pay),
                'basic':            float(e.basic),
                'hra':              float(e.hra),
                'da':               float(e.da),
                'pf_employee':      float(e.pf_employee),
                'esi_employee':     float(e.esi_employee),
                'pt':               float(e.pt),
                'tds':              float(e.tds),
                'lop_deduction':    float(e.lop_deduction),
                'total_deductions': float(e.total_deductions),
                'net_pay':          float(e.net_pay),
                'adjustments': [
                    {'type': adj.type, 'amount': float(adj.amount), 'reason': adj.reason}
                    for adj in e.adjustments.all()
                ],
            })

        ytd = {
            'gross':            sum(h['gross']            for h in history),
            'net_pay':          sum(h['net_pay']          for h in history),
            'pf_employee':      sum(h['pf_employee']      for h in history),
            'esi_employee':     sum(h['esi_employee']      for h in history),
            'pt':               sum(h['pt']               for h in history),
            'tds':              sum(h['tds']              for h in history),
            'lop_deduction':    sum(h['lop_deduction']    for h in history),
            'total_deductions': sum(h['total_deductions'] for h in history),
            'lop_days':         sum(h['lop_days']         for h in history),
            'ot_hours':         sum(h['ot_hours']         for h in history),
            'ot_pay':           sum(h['ot_pay']           for h in history),
            'months_paid':      len(history),
        }

        return Response({'year': year, 'ytd': ytd, 'history': history})


# ── DEDUCTION HISTORY — BY EMPLOYEE (Admin/HR) ────────────────────────────────

class EmployeeDeductionHistoryView(APIView):
    permission_classes = [make_permission('view_payroll')]

    def get(self, request, emp_id):
        year = request.query_params.get('year', date.today().year)

        try:
            emp = User.objects.get(pk=emp_id)
        except User.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=404)

        entries = PayrollEntry.objects.filter(
            employee            = emp,
            payroll_run__status = 'locked',
            payroll_run__year   = year,
        ).select_related('payroll_run', 'salary_structure').order_by(
            'payroll_run__year', 'payroll_run__month'
        )

        history = []
        for e in entries:
            run = e.payroll_run
            history.append({
                'entry_id':         e.id,
                'month':            run.month,
                'year':             run.year,
                'gross':            float(e.gross),
                'present_days':     float(e.present_days),
                'working_days':     int(e.working_days),
                'lop_days':         float(e.lop_days),
                'ot_hours':         float(e.ot_hours),
                'ot_pay':           float(e.ot_pay),
                'basic':            float(e.basic),
                'hra':              float(e.hra),
                'da':               float(e.da),
                'pf_employee':      float(e.pf_employee),
                'esi_employee':     float(e.esi_employee),
                'pt':               float(e.pt),
                'tds':              float(e.tds),
                'lop_deduction':    float(e.lop_deduction),
                'total_deductions': float(e.total_deductions),
                'net_pay':          float(e.net_pay),
                'adjustments': [
                    {'type': adj.type, 'amount': float(adj.amount), 'reason': adj.reason}
                    for adj in e.adjustments.all()
                ],
            })

        ytd = {
            'gross':            sum(h['gross']            for h in history),
            'net_pay':          sum(h['net_pay']          for h in history),
            'pf_employee':      sum(h['pf_employee']      for h in history),
            'esi_employee':     sum(h['esi_employee']     for h in history),
            'pt':               sum(h['pt']               for h in history),
            'tds':              sum(h['tds']              for h in history),
            'lop_deduction':    sum(h['lop_deduction']    for h in history),
            'total_deductions': sum(h['total_deductions'] for h in history),
            'lop_days':         sum(h['lop_days']         for h in history),
            'ot_hours':         sum(h['ot_hours']         for h in history),
            'ot_pay':           sum(h['ot_pay']           for h in history),
            'months_paid':      len(history),
        }

        return Response({
            'employee': {
                'id':       emp.id,
                'name':     emp.get_full_name() or emp.username,
                'email':    emp.email,
                'role':     emp.role,
                'emp_type': emp.employee_type,
                'emp_code': getattr(getattr(emp, 'profile', None), 'emp_code', ''),
            },
            'year':    year,
            'ytd':     ytd,
            'history': history,
        })


# ── ALL EMPLOYEES DEDUCTION SUMMARY (Admin/HR) ────────────────────────────────

class AllDeductionSummaryView(APIView):
    permission_classes = [make_permission('view_payroll')]

    def get(self, request):
        month = int(request.query_params.get('month', date.today().month))
        year  = int(request.query_params.get('year',  date.today().year))

        entries = PayrollEntry.objects.filter(
            payroll_run__month  = month,
            payroll_run__year   = year,
            payroll_run__status = 'locked',
        ).select_related(
            'employee', 'employee__profile', 'employee__profile__department',
        ).order_by('employee__first_name')

        data = []
        for e in entries:
            try:
                emp_code = e.employee.profile.emp_code
                dept     = e.employee.profile.department.name if e.employee.profile.department else '—'
            except Exception:
                emp_code = ''
                dept     = '—'

            data.append({
                'emp_id':           e.employee.id,
                'emp_code':         emp_code,
                'name':             e.employee.get_full_name() or e.employee.username,
                'department':       dept,
                'present_days':     float(e.present_days),
                'working_days':     int(e.working_days),
                'lop_days':         float(e.lop_days),
                'ot_hours':         float(e.ot_hours),
                'gross':            float(e.gross),
                'basic':            float(e.basic),
                'hra':              float(e.hra),
                'da':               float(e.da),
                'pf_employee':      float(e.pf_employee),
                'esi_employee':     float(e.esi_employee),
                'pt':               float(e.pt),
                'tds':              float(e.tds),
                'lop_deduction':    float(e.lop_deduction),
                'total_deductions': float(e.total_deductions),
                'net_pay':          float(e.net_pay),
                'has_lop':          e.lop_days > 0,
                'has_ot':           e.ot_hours > 0,
            })

        summary = {
            'total_employees':    len(data),
            'employees_with_lop': sum(1 for d in data if d['has_lop']),
            'employees_with_ot':  sum(1 for d in data if d['has_ot']),
            'total_gross':        sum(d['gross']            for d in data),
            'total_net':          sum(d['net_pay']          for d in data),
            'total_pf':           sum(d['pf_employee']      for d in data),
            'total_esi':          sum(d['esi_employee']     for d in data),
            'total_tds':          sum(d['tds']              for d in data),
            'total_lop':          sum(d['lop_deduction']    for d in data),
            'total_deductions':   sum(d['total_deductions'] for d in data),
            'total_lop_days':     sum(d['lop_days']         for d in data),
        }

        return Response({
            'month':   month,
            'year':    year,
            'summary': summary,
            'entries': data,
        })


# ── DASHBOARD STATS ───────────────────────────────────────────────────────────

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        from attendance.models import AttendanceRecord
        from leave.models import LeaveRequest, LeaveBalance
        from employees.models import EmployeeProfile

        today = date.today()
        if any(request.user.has_perm_code(code) for code in (
            'view_employees',
            'view_reports',
            'view_payroll',
            'process_payroll',
            'view_all_leave',
            'manage_settings',
        )):
            return self._admin_stats(request, today)
        elif any(request.user.has_perm_code(code) for code in (
            'view_team_attendance',
            'approve_leave',
            'view_team_tasks',
        )):
            return self._manager_stats(request, today)

        return self._employee_stats(request, today)

    def _employee_stats(self, request, today):
        from attendance.models import AttendanceRecord
        from leave.models import LeaveRequest, LeaveBalance

        att = AttendanceRecord.objects.filter(
            employee    = request.user,
            date__year  = today.year,
            date__month = today.month,
        )
        present = att.filter(status__in=['present', 'late']).count()
        absent  = att.filter(status='absent').count()
        lop     = att.filter(status='absent').count() + att.filter(status='half_day').count() * 0.5
        today_att = att.filter(date=today).first()

        balances = LeaveBalance.objects.filter(
            employee=request.user, year=today.year,
        ).select_related('leave_type')

        pending_leaves = LeaveRequest.objects.filter(
            employee=request.user, status='pending',
        ).count()

        last_payslip = PayrollEntry.objects.filter(
            employee=request.user, payroll_run__status='locked',
        ).select_related('payroll_run').order_by(
            '-payroll_run__year', '-payroll_run__month'
        ).first()

        return Response({
            'scope': 'personal',
            'attendance': {
                'present_this_month': present,
                'absent_this_month':  absent,
                'lop_this_month':     lop,
                'today_checked_in':   bool(today_att and today_att.check_in),
                'today_checked_out':  bool(today_att and today_att.check_out),
                'today_status':       today_att.status if today_att else 'not_started',
            },
            'leave': {
                'pending_requests': pending_leaves,
                'balances': [
                    {
                        'name':      b.leave_type.name,
                        'code':      b.leave_type.code,
                        'remaining': float(b.remaining),
                        'total':     float(b.total),
                    }
                    for b in balances
                ],
            },
            'last_payslip': {
                'month':            last_payslip.payroll_run.month if last_payslip else None,
                'year':             last_payslip.payroll_run.year  if last_payslip else None,
                'net_pay':          float(last_payslip.net_pay)          if last_payslip else 0,
                'gross':            float(last_payslip.gross)            if last_payslip else 0,
                'lop_days':         float(last_payslip.lop_days)         if last_payslip else 0,
                'lop_deduction':    float(last_payslip.lop_deduction)    if last_payslip else 0,
                'pf':               float(last_payslip.pf_employee)      if last_payslip else 0,
                'tds':              float(last_payslip.tds)              if last_payslip else 0,
                'total_deductions': float(last_payslip.total_deductions) if last_payslip else 0,
            },
        })

    def _admin_stats(self, request, today):
        from employees.models import EmployeeProfile
        from attendance.models import AttendanceRecord
        from leave.models import LeaveRequest

        total_emp  = User.objects.filter(is_active=True).count()
        total_dept = EmployeeProfile.objects.values('department').distinct().count()
        today_att  = AttendanceRecord.objects.filter(date=today)
        checked_in = today_att.filter(check_in__isnull=False).count()
        pending_leaves = LeaveRequest.objects.filter(status='pending').count()

        last_run = PayrollRun.objects.order_by('-year', '-month').first()
        last_run_data = None
        if last_run:
            entries = PayrollEntry.objects.filter(payroll_run=last_run)
            last_run_data = {
                'month':          last_run.month,
                'year':           last_run.year,
                'status':         last_run.status,
                'total_net':      float(sum(e.net_pay       for e in entries)),
                'total_gross':    float(sum(e.gross         for e in entries)),
                'total_pf':       float(sum(e.pf_employee   for e in entries)),
                'total_tds':      float(sum(e.tds           for e in entries)),
                'total_lop':      float(sum(e.lop_deduction for e in entries)),
                'employees_paid': entries.filter(payroll_run__status='locked').count(),
                'employees_lop':  entries.filter(lop_days__gt=0).count(),
            }

        return Response({
            'scope': 'company',
            'headcount': {
                'total_employees':   total_emp,
                'total_departments': total_dept,
                'checked_in_today':  checked_in,
                'pending_leaves':    pending_leaves,
            },
            'last_payroll': last_run_data,
        })

    def _manager_stats(self, request, today):
        from attendance.models import AttendanceRecord
        from leave.models import LeaveRequest

        team_ids   = User.objects.filter(profile__manager=request.user).values_list('id', flat=True)
        today_att  = AttendanceRecord.objects.filter(date=today, employee_id__in=team_ids)
        checked_in = today_att.filter(check_in__isnull=False).count()
        absent     = len(team_ids) - checked_in
        pending    = LeaveRequest.objects.filter(employee_id__in=team_ids, status='pending').count()

        return Response({
            'scope': 'team',
            'team': {
                'total':            len(team_ids),
                'checked_in_today': checked_in,
                'absent_today':     absent,
                'pending_leaves':   pending,
            },
        })
