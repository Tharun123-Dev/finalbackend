# payroll/serializers.py — FULL REPLACEMENT
from rest_framework import serializers
from .models import SalaryStructure, PayrollRun, PayrollEntry, PayrollAdjustment


class SalaryStructureSerializer(serializers.ModelSerializer):
    employee_name    = serializers.SerializerMethodField()
    emp_code         = serializers.SerializerMethodField()
    created_by       = serializers.PrimaryKeyRelatedField(read_only=True)

    # ── Computed properties from the model — exposed as read-only fields ──────
    # These are @property on the model, NOT database columns.
    # Must use SerializerMethodField so DRF calls the property getter.
    basic            = serializers.SerializerMethodField()
    hra              = serializers.SerializerMethodField()
    da               = serializers.SerializerMethodField()
    special_allowance= serializers.SerializerMethodField()
    pf_employee      = serializers.SerializerMethodField()
    esi_employee     = serializers.SerializerMethodField()
    gross            = serializers.SerializerMethodField()
    total_deductions = serializers.SerializerMethodField()
    net_pay          = serializers.SerializerMethodField()
    monthly_ctc      = serializers.SerializerMethodField()
    earnings_breakdown = serializers.SerializerMethodField()
    deductions_breakdown = serializers.SerializerMethodField()
    calculation_summary = serializers.SerializerMethodField()

    class Meta:
        model  = SalaryStructure
        fields = [
            'id',
            'employee',
            'employee_name',
            'emp_code',
            'effective_date',
            'ctc',
            'monthly_ctc',

            # percentages (stored in DB — editable)
            'basic_percent',
            'hra_percent',
            'da_percent',
            'pf_percent',
            'esi_percent',

            # fixed allowances (stored in DB — editable)
            'transport',
            'medical',
            'other_allowance',
            'pt',

            # computed values (from @property — read-only, always correct)
            'basic',
            'hra',
            'da',
            'special_allowance',
            'pf_employee',
            'esi_employee',
            'gross',
            'total_deductions',
            'net_pay',
            'earnings_breakdown',
            'deductions_breakdown',
            'calculation_summary',

            'is_active',
            'created_by',
            'created_at',
        ]

    # ── Identity helpers ──────────────────────────────────────────────────────

    def get_employee_name(self, obj):
        full = obj.employee.get_full_name().strip()
        return full if full else obj.employee.username

    def get_emp_code(self, obj):
        try:
            return obj.employee.profile.emp_code
        except Exception:
            return ''

    # ── Computed salary components — round to 2 decimal places ───────────────

    def get_monthly_ctc(self, obj):
        try:
            return round(float(obj.monthly_ctc), 2)
        except Exception:
            return 0.0

    def get_basic(self, obj):
        try:
            return round(float(obj.basic), 2)
        except Exception:
            return 0.0

    def get_hra(self, obj):
        try:
            return round(float(obj.hra), 2)
        except Exception:
            return 0.0

    def get_da(self, obj):
        try:
            return round(float(obj.da), 2)
        except Exception:
            return 0.0

    def get_special_allowance(self, obj):
        try:
            val = float(obj.special_allowance)
            return round(max(val, 0.0), 2)   # never negative
        except Exception:
            return 0.0

    def get_pf_employee(self, obj):
        try:
            return round(float(obj.pf_employee), 2)
        except Exception:
            return 0.0

    def get_esi_employee(self, obj):
        try:
            return round(float(obj.esi_employee), 2)
        except Exception:
            return 0.0

    def get_gross(self, obj):
        try:
            return round(float(obj.gross), 2)
        except Exception:
            return 0.0

    def get_total_deductions(self, obj):
        try:
            return round(float(obj.total_deductions), 2)
        except Exception:
            return 0.0

    def get_net_pay(self, obj):
        try:
            return round(float(obj.net_pay), 2)
        except Exception:
            return 0.0

    def get_earnings_breakdown(self, obj):
        return {
            'basic': self.get_basic(obj),
            'hra': self.get_hra(obj),
            'da': self.get_da(obj),
            'special_allowance': self.get_special_allowance(obj),
            'transport': round(float(obj.transport or 0), 2),
            'medical': round(float(obj.medical or 0), 2),
            'other_allowance': round(float(obj.other_allowance or 0), 2),
            'gross': self.get_gross(obj),
        }

    def get_deductions_breakdown(self, obj):
        return {
            'pf_employee': self.get_pf_employee(obj),
            'esi_employee': self.get_esi_employee(obj),
            'pt': round(float(obj.pt or 0), 2),
            'total_deductions': self.get_total_deductions(obj),
            'net_pay': self.get_net_pay(obj),
        }

    def get_calculation_summary(self, obj):
        return {
            'ctc': round(float(obj.ctc or 0), 2),
            'monthly_ctc': self.get_monthly_ctc(obj),
            'basic_percent': round(float(obj.basic_percent or 0), 2),
            'hra_percent': round(float(obj.hra_percent or 0), 2),
            'da_percent': round(float(obj.da_percent or 0), 2),
            'pf_percent': round(float(obj.pf_percent or 0), 2),
            'esi_percent': round(float(obj.esi_percent or 0), 2),
            'effective_date': str(obj.effective_date),
        }


# ─────────────────────────────────────────────────────────────────────────────

class AdjustmentSerializer(serializers.ModelSerializer):
    added_by_name = serializers.SerializerMethodField()

    class Meta:
        model  = PayrollAdjustment
        fields = ['id', 'type', 'amount', 'reason', 'added_by', 'added_by_name', 'created_at']

    def get_added_by_name(self, obj):
        if obj.added_by:
            return obj.added_by.get_full_name() or obj.added_by.username
        return None


class PayrollRunSerializer(serializers.ModelSerializer):
    processed_by_name = serializers.SerializerMethodField()
    approved_by_name  = serializers.SerializerMethodField()
    entry_count       = serializers.SerializerMethodField()
    total_net_pay     = serializers.SerializerMethodField()
    period_label      = serializers.SerializerMethodField()

    class Meta:
        model  = PayrollRun
        fields = [
            'id', 'month', 'year', 'period_start', 'period_end',
            'period_label', 'status', 'notes',
            'processed_by', 'processed_by_name',
            'approved_by',  'approved_by_name',
            'entry_count',  'total_net_pay',
            'created_at',   'locked_at',
        ]

    def get_processed_by_name(self, obj):
        return obj.processed_by.get_full_name() if obj.processed_by else None

    def get_approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else None

    def get_entry_count(self, obj):
        return obj.entries.count()

    def get_total_net_pay(self, obj):
        return float(sum(e.net_pay for e in obj.entries.all()))

    def get_period_label(self, obj):
        return obj.period_label


class PayrollEntrySerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    emp_code      = serializers.SerializerMethodField()
    department    = serializers.SerializerMethodField()
    adjustments   = AdjustmentSerializer(many=True, read_only=True)
    payroll_run   = PayrollRunSerializer(read_only=True)
    earnings_breakdown = serializers.SerializerMethodField()
    deductions_breakdown = serializers.SerializerMethodField()
    attendance_breakdown = serializers.SerializerMethodField()
    calculation_summary = serializers.SerializerMethodField()

    class Meta:
        model  = PayrollEntry
        fields = [
            'id', 'payroll_run', 'employee', 'employee_name', 'emp_code', 'department',
            'total_days', 'working_days', 'present_days', 'lop_days', 'ot_hours',
            'holiday_count', 'holiday_names',
            'extra_work_days', 'extra_work_pay', 'extra_work_dates', 'comp_off_days',
            'basic', 'hra', 'da', 'special_allowance', 'transport', 'medical',
            'other_allowance', 'ot_pay',
            'pf_employee', 'esi_employee', 'pt', 'tds', 'lop_deduction',
            'gross', 'total_deductions', 'net_pay',
            'earnings_breakdown', 'deductions_breakdown', 'attendance_breakdown', 'calculation_summary',
            'is_paid', 'payslip_url', 'adjustments', 'created_at',
        ]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name() or obj.employee.username

    def get_emp_code(self, obj):
        try:   return obj.employee.profile.emp_code
        except: return ''

    def get_department(self, obj):
        try:   return obj.employee.profile.department.name if obj.employee.profile.department else ''
        except: return ''

    def get_earnings_breakdown(self, obj):
        adjustments = list(obj.adjustments.all())
        credits = sum(
            float(adj.amount) for adj in adjustments
            if adj.type in ('bonus', 'reimbursement', 'arrear')
        )
        return {
            'basic': float(obj.basic),
            'hra': float(obj.hra),
            'da': float(obj.da),
            'special_allowance': float(obj.special_allowance),
            'transport': float(obj.transport),
            'medical': float(obj.medical),
            'other_allowance': float(obj.other_allowance),
            'ot_pay': float(obj.ot_pay),
            'extra_work_pay': float(obj.extra_work_pay),
            'adjustment_credits': credits,
            'gross': float(obj.gross),
        }

    def get_deductions_breakdown(self, obj):
        adjustments = list(obj.adjustments.all())
        adjustment_deductions = sum(
            float(adj.amount) for adj in adjustments
            if adj.type == 'deduction'
        )
        return {
            'pf_employee': float(obj.pf_employee),
            'esi_employee': float(obj.esi_employee),
            'pt': float(obj.pt),
            'tds': float(obj.tds),
            'lop_deduction': float(obj.lop_deduction),
            'adjustment_deductions': adjustment_deductions,
            'total_deductions': float(obj.total_deductions),
            'net_pay': float(obj.net_pay),
        }

    def get_attendance_breakdown(self, obj):
        return {
            'total_days': obj.total_days,
            'working_days': obj.working_days,
            'present_days': float(obj.present_days),
            'lop_days': float(obj.lop_days),
            'holiday_count': obj.holiday_count,
            'holiday_names': obj.holiday_names,
            'ot_hours': float(obj.ot_hours),
            'extra_work_days': float(obj.extra_work_days),
            'extra_work_dates': obj.extra_work_dates,
            'comp_off_days': float(obj.comp_off_days),
        }

    def get_calculation_summary(self, obj):
        per_day_gross = float(obj.gross / obj.working_days) if obj.working_days else 0
        return {
            'period': obj.payroll_run.period_label if obj.payroll_run_id else '',
            'status': obj.payroll_run.status if obj.payroll_run_id else '',
            'per_day_gross': round(per_day_gross, 2),
            'formula': 'gross - (pf + esi + pt + tds + lop + adjustment deductions) + adjustment credits',
        }
