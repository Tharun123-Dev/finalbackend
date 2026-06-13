from django.conf import settings
from django.db import models


class SupportTicketType(models.Model):
    tenant_id = models.CharField(max_length=64, default='default', db_index=True)
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=80)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='created_support_ticket_types'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['tenant_id', 'code']
        ordering = ['name']

    def __str__(self):
        return f"{self.tenant_id} | {self.name}"


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('waiting_user', 'Waiting for User'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('reopened', 'Reopened'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    tenant_id = models.CharField(max_length=64, default='default', db_index=True)
    ticket_no = models.CharField(max_length=30, unique=True, blank=True)
    issue_type = models.ForeignKey(
        SupportTicketType, on_delete=models.PROTECT, related_name='tickets'
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='support_tickets'
    )
    subject = models.CharField(max_length=180)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='assigned_support_tickets'
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='resolved_support_tickets'
    )
    resolution_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'requester']),
            models.Index(fields=['tenant_id', 'priority']),
        ]

    def __str__(self):
        return f"{self.ticket_no or self.pk} | {self.subject}"

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating and not self.ticket_no:
            self.ticket_no = f"SUP-{self.tenant_id[:4].upper()}-{self.pk:05d}"
            super().save(update_fields=['ticket_no'])


class SupportTicketNote(models.Model):
    ticket = models.ForeignKey(
        SupportTicket, on_delete=models.CASCADE, related_name='notes'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='support_ticket_notes'
    )
    note = models.TextField()
    status_from = models.CharField(max_length=20, blank=True)
    status_to = models.CharField(max_length=20, blank=True)
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.ticket.ticket_no} | {self.author.username}"
