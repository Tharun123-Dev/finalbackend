# leave/models.py
from django.db import models
from accounts.models import User


class LeaveType(models.Model):
    EMPLOYEE_TYPES = [
        ('all',      'All'),
        ('regular',  'Regular'),
        ('contract', 'Contract'),
        ('parttime', 'Part-Time'),
        ('intern',   'Intern'),
    ]

    tenant_id         = models.CharField(max_length=64, default='default', db_index=True)
    name              = models.CharField(max_length=100)
    code              = models.CharField(max_length=20)
    days_allowed      = models.IntegerField(default=0)
    applicable_to     = models.CharField(max_length=20, choices=EMPLOYEE_TYPES, default='all')
    carry_forward     = models.BooleanField(default=False)
    max_carry_forward = models.IntegerField(default=0)
    is_paid           = models.BooleanField(default=True)
    requires_document = models.BooleanField(default=False)
    min_notice_days   = models.IntegerField(default=0)
    is_active         = models.BooleanField(default=True)
    description       = models.TextField(blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = [['tenant_id', 'name'], ['tenant_id', 'code']]

    def __str__(self):
        return f"{self.name} ({self.code})"


class LeaveBalance(models.Model):
    tenant_id  = models.CharField(max_length=64, default='default', db_index=True)
    employee   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='balances')
    year       = models.IntegerField()
    total      = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    used       = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    pending    = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    carried    = models.DecimalField(max_digits=5, decimal_places=1, default=0)

    class Meta:
        unique_together = ['employee', 'leave_type', 'year']
        ordering        = ['leave_type__name']

    @property
    def remaining(self):
        return max(self.total - self.used - self.pending, 0)

    def __str__(self):
        return f"{self.employee.username} | {self.leave_type.name} | {self.year}"

    def save(self, *args, **kwargs):
        if (not self.tenant_id or self.tenant_id == 'default') and self.employee_id:
            self.tenant_id = getattr(self.employee, 'tenant_id', 'default') or 'default'
        super().save(*args, **kwargs)


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('approved',  'Approved'),
        ('rejected',  'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    SESSION_CHOICES = [
        ('full',      'Full Day'),
        ('first_half', 'First Half'),
        ('second_half', 'Second Half'),
    ]

    tenant_id    = models.CharField(max_length=64, default='default', db_index=True)
    employee     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type   = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='requests')
    start_date   = models.DateField()
    end_date     = models.DateField()
    days         = models.DecimalField(max_digits=4, decimal_places=1)
    session      = models.CharField(max_length=20, choices=SESSION_CHOICES, default='full')
    reason       = models.TextField()
    doc_url      = models.URLField(blank=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by  = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='approved_leaves'
    )
    approver_note = models.TextField(blank=True)
    applied_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.employee.username} | {self.leave_type.name} | {self.start_date} | {self.status}"

    def save(self, *args, **kwargs):
        if (not self.tenant_id or self.tenant_id == 'default') and self.employee_id:
            self.tenant_id = getattr(self.employee, 'tenant_id', 'default') or 'default'
        super().save(*args, **kwargs)
