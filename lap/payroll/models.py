import calendar
from datetime import date
from django.db import models

# Create your models here.
# payroll/models.py
from django.db import models
from accounts.models import User

class SalaryStructure(models.Model):
    tenant_id = models.CharField(max_length=64, default='default', db_index=True)

    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='salary_structures'
    )

    effective_date = models.DateField()

    ctc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # Dynamic Percentage Configuration
    basic_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=40
    )

    hra_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50
    )

    da_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10
    )

    pf_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=12
    )

    esi_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.75
    )

    # Fixed Allowances
    transport = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1600
    )

    medical = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1250
    )

    other_allowance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Professional Tax
    pt = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=200
    )

    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_structures'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-effective_date']

    def __str__(self):
        return (
            f"{self.employee.username} | "
            f"{self.effective_date} | "
            f"CTC {self.ctc}"
        )

    def save(self, *args, **kwargs):
        if (not self.tenant_id or self.tenant_id == 'default') and self.employee_id:
            self.tenant_id = getattr(self.employee, 'tenant_id', 'default') or 'default'
        super().save(*args, **kwargs)

    @property
    def monthly_ctc(self):

        return self.ctc / 12

    @property
    def basic(self):

        return (
            self.monthly_ctc *
            self.basic_percent /
            100
        )

    @property
    def hra(self):

        return (
            self.basic *
            self.hra_percent /
            100
        )

    @property
    def da(self):

        return (
            self.basic *
            self.da_percent /
            100
        )

    @property
    def special_allowance(self):

        return (
            self.monthly_ctc
            - self.basic
            - self.hra
            - self.da
            - self.transport
            - self.medical
            - self.other_allowance
        )

    @property
    def pf_employee(self):

        return (
            self.basic *
            self.pf_percent /
            100
        )

    @property
    def esi_employee(self):

        return (
            self.gross *
            self.esi_percent /
            100
        )

    @property
    def gross(self):

        return (
            self.basic
            + self.hra
            + self.da
            + self.special_allowance
            + self.transport
            + self.medical
            + self.other_allowance
        )

    @property
    def total_deductions(self):

        return (
            self.pf_employee
            + self.esi_employee
            + self.pt
        )

    @property
    def net_pay(self):

        return (
            self.gross
            - self.total_deductions
        )

class PayrollRun(models.Model):
    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('processed', 'Processed'),
        ('approved',  'Approved'),
        ('locked',    'Locked'),
    ]

    tenant_id    = models.CharField(max_length=64, default='default', db_index=True)
    month        = models.IntegerField()
    year         = models.IntegerField()
    period_start = models.DateField(null=True, blank=True)
    period_end   = models.DateField(null=True, blank=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    processed_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='payroll_runs'
    )
    approved_by  = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='approved_payroll_runs'
    )
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    locked_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['tenant_id', 'month', 'year', 'period_start', 'period_end']
        ordering        = ['-year', '-month', '-period_start']

    def __str__(self):
        return f"Payroll {self.month}/{self.year} ({self.period_label}) - {self.status}"

    def save(self, *args, **kwargs):
        if not self.period_start or not self.period_end:
            last_day = calendar.monthrange(self.year, self.month)[1]
            self.period_start = date(self.year, self.month, 1)
            self.period_end = date(self.year, self.month, last_day)
        super().save(*args, **kwargs)

    @property
    def period_label(self):
        if not self.period_start or not self.period_end:
            return 'Full month'
        last_day = calendar.monthrange(self.year, self.month)[1]
        if self.period_start.day == 1 and self.period_end.day == last_day:
            return 'Full month'
        return f"{self.period_start.day}-{self.period_end.day}"


class PayrollEntry(models.Model):
    tenant_id       = models.CharField(max_length=64, default='default', db_index=True)
    payroll_run    = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='entries')
    employee       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payroll_entries')
    salary_structure = models.ForeignKey(SalaryStructure, null=True, on_delete=models.SET_NULL)

    # Attendance snapshot
    total_days     = models.IntegerField(default=0)
    working_days   = models.IntegerField(default=0)
    present_days   = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    lop_days       = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    ot_hours       = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    # Public holidays this month — stored so payslip can display them
    holiday_count  = models.IntegerField(default=0)
    holiday_names  = models.JSONField(default=list, blank=True)  # e.g. ["Diwali", "Dussehra"]
    extra_work_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    extra_work_pay  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    extra_work_dates = models.JSONField(default=list, blank=True)
    comp_off_days   = models.DecimalField(max_digits=5, decimal_places=1, default=0)

    # Earnings (pro-rated)
    basic          = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hra            = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    da             = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    special_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    medical        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ot_pay         = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Deductions
    pf_employee    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    esi_employee   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pt             = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tds            = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lop_deduction  = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Totals
    gross          = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_pay        = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    payslip_url    = models.URLField(blank=True)
    is_paid        = models.BooleanField(default=False)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['payroll_run', 'employee']

    def __str__(self):
        return f"{self.employee.username} | {self.payroll_run}"

    def save(self, *args, **kwargs):
        if not self.tenant_id or self.tenant_id == 'default':
            if self.payroll_run_id:
                self.tenant_id = self.payroll_run.tenant_id
            elif self.employee_id:
                self.tenant_id = getattr(self.employee, 'tenant_id', 'default') or 'default'
        super().save(*args, **kwargs)


class PayrollAdjustment(models.Model):
    TYPE_CHOICES = [
        ('bonus',       'Bonus'),
        ('reimbursement', 'Reimbursement'),
        ('deduction',   'Deduction'),
        ('arrear',      'Arrear'),
    ]

    tenant_id     = models.CharField(max_length=64, default='default', db_index=True)
    payroll_entry = models.ForeignKey(PayrollEntry, on_delete=models.CASCADE, related_name='adjustments')
    type         = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount       = models.DecimalField(max_digits=10, decimal_places=2)
    reason       = models.TextField()
    added_by     = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name='adjustments_added'
    )
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} | {self.amount} | {self.payroll_entry.employee.username}"

    def save(self, *args, **kwargs):
        if (not self.tenant_id or self.tenant_id == 'default') and self.payroll_entry_id:
            self.tenant_id = self.payroll_entry.tenant_id
        super().save(*args, **kwargs)


class PayrollCarryForwardAdjustment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('applied', 'Applied'),
        ('ignored', 'Ignored'),
    ]

    tenant_id = models.CharField(max_length=64, default='default', db_index=True)
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payroll_carry_forward_adjustments')
    source_run = models.ForeignKey(
        PayrollRun, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='carry_forward_sources'
    )
    source_regularization = models.ForeignKey(
        'attendance.AttendanceRegularization', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='payroll_corrections'
    )
    source_month = models.IntegerField()
    source_year = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_entry = models.ForeignKey(
        PayrollEntry, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='applied_carry_forward_adjustments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.employee.username} | {self.source_month}/{self.source_year} | {self.amount} | {self.status}"

    def save(self, *args, **kwargs):
        if (not self.tenant_id or self.tenant_id == 'default') and self.employee_id:
            self.tenant_id = getattr(self.employee, 'tenant_id', 'default') or 'default'
        super().save(*args, **kwargs)
