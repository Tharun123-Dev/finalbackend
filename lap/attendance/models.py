# attendance/models.py
import math
from django.db import models
from accounts.models import User


# ── OFFICE LOCATION (admin-configurable) ──────────────────────────────────────

class OfficeLocation(models.Model):
    """
    Stores the office GPS co-ordinates.
    Only one active record is used at a time (is_active=True).
    Admins can update latitude/longitude dynamically from the admin panel
    or via API — no code change needed.
    """
    tenant_id   = models.CharField(max_length=64, default='default', db_index=True)
    name        = models.CharField(max_length=100, default='Head Office')
    latitude    = models.DecimalField(max_digits=9, decimal_places=6)
    longitude   = models.DecimalField(max_digits=9, decimal_places=6)
    radius_meters = models.PositiveIntegerField(default=300,
                    help_text='Allowed check-in radius in metres')
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', '-updated_at']

    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude}) r={self.radius_meters}m"

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        """Return distance in metres between two GPS co-ordinates."""
        R = 6_371_000  # Earth radius in metres
        phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
        dphi  = math.radians(float(lat2) - float(lat1))
        dlambda = math.radians(float(lon2) - float(lon1))
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * R * math.asin(math.sqrt(a))

    @classmethod
    def active(cls):
        """Return the currently active office location or None."""
        return cls.objects.filter(is_active=True).first()

    @classmethod
    def active_for_tenant(cls, tenant_id):
        """Return the active office location for this tenant, falling back to default."""
        tenant_id = str(tenant_id or 'default')
        return (
            cls.objects.filter(tenant_id=tenant_id, is_active=True).first()
            or cls.objects.filter(tenant_id='default', is_active=True).first()
        )

    def distance_from(self, lat, lon):
        """Return metres from this office to the given GPS point."""
        return self.haversine(self.latitude, self.longitude, lat, lon)


# ── ATTENDANCE RECORD ─────────────────────────────────────────────────────────

class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present',  'Present'),
        ('absent',   'Absent'),
        ('half_day', 'Half Day'),
        ('late',     'Late'),
        ('holiday',  'Holiday'),
        ('weekend',  'Weekend'),
        ('leave',    'On Leave'),
        ('pending',  'Pending Correction'),
    ]
    SHIFT_CHOICES = [
        ('day', 'Day Shift'),
        ('night', 'Night Shift'),
    ]

    tenant_id    = models.CharField(max_length=64, default='default', db_index=True)
    employee     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    date         = models.DateField()
    shift_type   = models.CharField(max_length=10, choices=SHIFT_CHOICES, default='day')
    check_in     = models.TimeField(null=True, blank=True)
    check_out    = models.TimeField(null=True, blank=True)
    check_in_at  = models.DateTimeField(null=True, blank=True)
    check_out_at = models.DateTimeField(null=True, blank=True)
    hours_worked = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='absent')
    is_wfh       = models.BooleanField(default=False)
    ot_hours     = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    note         = models.TextField(blank=True)
    is_locked    = models.BooleanField(default=False)
    shift_start_snapshot = models.TimeField(null=True, blank=True)
    shift_end_snapshot = models.TimeField(null=True, blank=True)
    grace_minutes_snapshot = models.PositiveIntegerField(null=True, blank=True)
    standard_hours_snapshot = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    half_day_hours_snapshot = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    is_overnight_shift = models.BooleanField(default=False)

    # ── Location tracking ─────────────────────────────────────────────────────
    checkin_latitude   = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    checkin_longitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    checkout_latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    checkout_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    checkin_distance_m  = models.FloatField(null=True, blank=True,
                          help_text='Distance from office at check-in (metres)')
    checkout_distance_m = models.FloatField(null=True, blank=True,
                          help_text='Distance from office at check-out (metres)')

    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'date', 'shift_type']
        ordering        = ['-date']

    def __str__(self):
        return f"{self.employee.username} | {self.date} | {self.shift_type} | {self.status}"

    def save(self, *args, **kwargs):
        if (not self.tenant_id or self.tenant_id == 'default') and self.employee_id:
            self.tenant_id = getattr(self.employee, 'tenant_id', 'default') or 'default'
        super().save(*args, **kwargs)

    def calculate_hours(self):
        if not self.check_in or not self.check_out:
            return 0
        if self.check_in_at and self.check_out_at:
            diff = (self.check_out_at - self.check_in_at).total_seconds() / 3600
            return round(max(diff, 0), 2)
        from datetime import datetime, date, timedelta
        ci = datetime.combine(date.today(), self.check_in)
        co = datetime.combine(date.today(), self.check_out)
        if co <= ci:
            co += timedelta(days=1)
        diff = (co - ci).total_seconds() / 3600
        return round(max(diff, 0), 2)

    def expected_shift_end_at(self):
        if not self.check_in:
            return None
        from datetime import datetime, timedelta
        from django.utils import timezone
        shift_end = self.shift_end_snapshot or self.check_in
        naive_end = datetime.combine(self.date, shift_end)
        if self.is_overnight_shift or (self.shift_start_snapshot and shift_end <= self.shift_start_snapshot):
            naive_end += timedelta(days=1)
        if timezone.is_naive(naive_end):
            return timezone.make_aware(naive_end, timezone.get_current_timezone())
        return naive_end


# ── ATTENDANCE REGULARIZATION ─────────────────────────────────────────────────

class AttendanceRegularization(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    tenant_id    = models.CharField(max_length=64, default='default', db_index=True)
    attendance   = models.OneToOneField(
        AttendanceRecord, on_delete=models.CASCADE,
        related_name='regularization'
    )
    employee     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='regularizations')
    reason       = models.TextField()
    requested_checkin  = models.TimeField(null=True, blank=True)
    requested_checkout = models.TimeField(null=True, blank=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by  = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='approved_regularizations'
    )
    approver_note = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.username} | {self.attendance.date} | {self.status}"

    def save(self, *args, **kwargs):
        if (not self.tenant_id or self.tenant_id == 'default') and self.employee_id:
            self.tenant_id = getattr(self.employee, 'tenant_id', 'default') or 'default'
        super().save(*args, **kwargs)


# ── HOLIDAY ───────────────────────────────────────────────────────────────────

class Holiday(models.Model):
    tenant_id   = models.CharField(max_length=64, default='default', db_index=True)
    date        = models.DateField()
    name        = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']
        unique_together = ['tenant_id', 'date']

    def __str__(self):
        return f"{self.date} — {self.name}"
