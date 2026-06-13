# affiliate/admin.py
from django.contrib import admin
from .models import Affiliate, Referral, Commission, Payment, AffiliateNotification


@admin.register(Affiliate)
class AffiliateAdmin(admin.ModelAdmin):
    list_display = ['user', 'referral_code', 'total_earnings', 'paid_earnings', 'total_clicks', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'referral_code']
    readonly_fields = ['id', 'created_at']


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['customer_email', 'customer_name', 'affiliate', 'status', 'purchase_amount', 'referred_at']
    list_filter = ['status']
    search_fields = ['customer_email', 'customer_name']


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ['affiliate', 'amount', 'status', 'created_at']
    list_filter = ['status']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['affiliate', 'amount', 'payment_method', 'status', 'paid_at']
    list_filter = ['status']


@admin.register(AffiliateNotification)
class AffiliateNotificationAdmin(admin.ModelAdmin):
    list_display = ['affiliate', 'type', 'message', 'is_read', 'created_at']
    list_filter = ['type', 'is_read']