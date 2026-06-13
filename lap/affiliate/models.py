# affiliate/models.py
import uuid
import random
import string
from django.db import models
from django.conf import settings


def generate_referral_code(full_name):
    base = "".join(full_name.split())[:5].upper()
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{base}{suffix}"


class Affiliate(models.Model):
    """
    Affiliate profile linked to LAP's existing accounts.User.
    One user = one affiliate profile.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='affiliate_profile'
    )
    referral_code = models.CharField(max_length=20, unique=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    bank_account_details = models.CharField(max_length=255, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    payout_method = models.CharField(max_length=50, default='ACH/Direct Deposit')
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    profile_image_url = models.URLField(blank=True, null=True)
    total_earnings = models.FloatField(default=0.0)
    paid_earnings = models.FloatField(default=0.0)
    total_clicks = models.IntegerField(default=0)
    active_campaigns = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Affiliate: {self.user.get_full_name() or self.user.username} [{self.referral_code}]"

    @property
    def pending_earnings(self):
        return self.total_earnings - self.paid_earnings

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def email(self):
        return self.user.email


class Referral(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('converted', 'Converted'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    affiliate = models.ForeignKey(
        Affiliate, on_delete=models.CASCADE, related_name='referrals'
    )
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    purchase_amount = models.FloatField(default=0.0)
    referred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-referred_at']

    def __str__(self):
        return f"Referral {self.customer_email} -> {self.affiliate.referral_code}"


class Commission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referral = models.OneToOneField(
        Referral, on_delete=models.CASCADE, related_name='commission'
    )
    affiliate = models.ForeignKey(
        Affiliate, on_delete=models.CASCADE, related_name='commissions'
    )
    amount = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Commission ₹{self.amount} for {self.affiliate.referral_code}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    affiliate = models.ForeignKey(
        Affiliate, on_delete=models.CASCADE, related_name='payments'
    )
    amount = models.FloatField()
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    paid_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_at']

    def __str__(self):
        return f"Payment ₹{self.amount} to {self.affiliate.referral_code}"


class AffiliateNotification(models.Model):
    """
    Affiliate-specific notifications.
    Named AffiliateNotification to avoid clash with LAP's notifications app.
    """
    TYPE_CHOICES = [
        ('commission', 'Commission'),
        ('referral', 'Referral'),
        ('payment', 'Payment'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    affiliate = models.ForeignKey(
        Affiliate, on_delete=models.CASCADE, related_name='affiliate_notifications'
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.type}] {self.message[:50]}"