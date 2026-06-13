# notifications/models.py
from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('leave_applied',      'Leave Applied'),
        ('leave_approved',     'Leave Approved'),
        ('leave_rejected',     'Leave Rejected'),
        ('leave_cancelled',    'Leave Cancelled'),
        ('attendance_absent',  'Attendance Absent'),
        ('regularization',     'Regularization Request'),
        ('payroll_processed',  'Payroll Processed'),
        ('leave_balance_low',  'Leave Balance Low'),
        ('new_account',        'New Account Created'),
        ('general',            'General'),
        ('policy_updated',     'Policy Updated'),
    ]

    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title      = models.CharField(max_length=200)
    body       = models.TextField()
    type       = models.CharField(max_length=30, choices=TYPE_CHOICES, default='general')
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.type}] {self.user.username}: {self.title}"


class SystemSetting(models.Model):
    """
    Key-value store for ALL company-wide policies.
    Every policy is stored here and drives all modules dynamically.
    No hardcoding anywhere — always read from this table.
    """
    CATEGORIES = [
        ('attendance', 'Attendance'),
        ('leave',      'Leave'),
        ('payroll',    'Payroll'),
        ('general',    'General'),
        ('policy',     'Policies'),
    ]

    VALUE_TYPES = [
        ('integer',  'Integer'),
        ('decimal',  'Decimal'),
        ('boolean',  'Boolean (true/false)'),
        ('string',   'Text'),
        ('json',     'JSON'),
        ('time',     'Time (HH:MM)'),
    ]

    tenant_id    = models.CharField(max_length=64, default='default', db_index=True)
    key          = models.CharField(max_length=100)
    value        = models.TextField()
    value_type   = models.CharField(max_length=20, choices=VALUE_TYPES, default='string')
    label        = models.CharField(max_length=200)
    category     = models.CharField(max_length=30, choices=CATEGORIES, default='general')
    description  = models.TextField(blank=True)
    updated_at   = models.DateTimeField(auto_now=True)
    updated_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='updated_settings'
    )

    class Meta:
        ordering = ['category', 'key']
        unique_together = ['tenant_id', 'key']

    def __str__(self):
        return f"{self.category} | {self.key} = {self.value}"

    def get_value(self):
        """Returns value cast to correct Python type."""
        if self.value_type == 'integer':
            return int(self.value) if self.value else 0
        if self.value_type == 'decimal':
            return float(self.value) if self.value else 0.0
        if self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes')
        if self.value_type == 'json':
            import json
            return json.loads(self.value) if self.value else {}
        return self.value
