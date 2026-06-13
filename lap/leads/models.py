from django.db import models
from django.conf import settings


class LeadStatus(models.TextChoices):
    NEW = 'New', 'New'
    CONTACTED = 'Contacted', 'Contacted'
    INTERESTED = 'Interested', 'Interested'
    FOLLOW_UP_PENDING = 'Follow-Up Pending', 'Follow-Up Pending'
    ADMISSION_CONFIRMED = 'Admission Confirmed', 'Admission Confirmed'
    REJECTED = 'Rejected', 'Rejected'


class FieldType(models.TextChoices):
    TEXT = 'text', 'Text'
    EMAIL = 'email', 'Email'
    NUMBER = 'number', 'Number'
    DROPDOWN = 'dropdown', 'Dropdown'
    CHECKBOX = 'checkbox', 'Checkbox'
    RADIO = 'radio', 'Radio'
    DATE = 'date', 'Date'
    TEXTAREA = 'textarea', 'Textarea'
    FILE = 'file', 'File'


class LeadForm(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lead_forms'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class LeadOption(models.Model):
    CATEGORY_CHOICES = [
        ('status', 'Status'),
        ('contact_method', 'Contact Method'),
    ]

    tenant_id = models.CharField(max_length=64, default='default', db_index=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    color = models.CharField(max_length=30, blank=True, default='')
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)

    class Meta:
        db_table = 'lead_options'
        ordering = ['category', 'sort_order', 'id']
        unique_together = ['tenant_id', 'category', 'value']

    def __str__(self):
        return f"{self.category}: {self.label}"


class LeadField(models.Model):
    form = models.ForeignKey(
        LeadForm, on_delete=models.CASCADE, related_name='fields'
    )
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=50, choices=FieldType.choices)
    required = models.BooleanField(default=False)
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    section = models.CharField(max_length=255, default='General Details')
    validation = models.JSONField(blank=True, null=True)
    is_core = models.BooleanField(default=False)
    options = models.JSONField(blank=True, null=True)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'lead_fields'
        ordering = ['order']

    def __str__(self):
        return f"{self.form.name} — {self.label}"


class Lead(models.Model):
    full_name = models.CharField(max_length=255, db_index=True)
    email = models.EmailField(blank=True, null=True, db_index=True)
    phone = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    status = models.CharField(
        max_length=50, choices=LeadStatus.choices, default=LeadStatus.NEW
    )
    revenue_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=50, default='Unpaid')
    payment_reference = models.CharField(max_length=120, blank=True, default='')
    counselor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads'
    )
    form = models.ForeignKey(
        LeadForm,
        on_delete=models.PROTECT,
        related_name='leads'
    )
    tenant_id = models.CharField(max_length=64, default='default', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leads'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.status})"


class LeadFieldValue(models.Model):
    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, related_name='field_values'
    )
    field = models.ForeignKey(
        LeadField, on_delete=models.CASCADE
    )
    value = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'lead_field_values'

    def __str__(self):
        return f"Lead {self.lead_id} — {self.field.label}: {self.value}"


class FollowUp(models.Model):
    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, related_name='followups'
    )
    counselor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='lead_followups'
    )
    note = models.TextField()
    scheduled_at = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lead_followups'
        ordering = ['scheduled_at']

    def __str__(self):
        return f"FollowUp for Lead {self.lead_id} at {self.scheduled_at}"


class LeadNotification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lead_notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lead_notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user_id}: {self.title}"
