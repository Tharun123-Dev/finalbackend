# affiliate/serializers.py
from rest_framework import serializers
from .models import Affiliate, Referral, Commission, Payment, AffiliateNotification


class AffiliateProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    pending_earnings = serializers.FloatField(read_only=True)

    class Meta:
        model = Affiliate
        fields = [
            'id', 'full_name', 'email', 'referral_code',
            'phone', 'address', 'bank_account_details',
            'bank_name', 'account_number', 'payout_method', 'upi_id',
            'profile_image_url', 'total_earnings', 'paid_earnings',
            'pending_earnings', 'total_clicks', 'active_campaigns', 'created_at',
        ]
        read_only_fields = [
            'id', 'referral_code', 'total_earnings', 'paid_earnings',
            'total_clicks', 'active_campaigns', 'created_at'
        ]

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_email(self, obj):
        return obj.user.email


class AffiliateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Affiliate
        fields = [
            'phone', 'address', 'bank_account_details',
            'bank_name', 'account_number', 'payout_method', 'upi_id',
            'profile_image_url',
        ]


class AffiliateRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50, required=False, default='')
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    bank_account_details = serializers.CharField(required=False, allow_blank=True)
    bank_name = serializers.CharField(required=False, allow_blank=True)
    account_number = serializers.CharField(required=False, allow_blank=True)
    payout_method = serializers.CharField(required=False, default='ACH/Direct Deposit')
    upi_id = serializers.CharField(required=False, allow_blank=True)


class ReferralSerializer(serializers.ModelSerializer):
    affiliate_name = serializers.SerializerMethodField()
    affiliate_code = serializers.CharField(source='affiliate.referral_code', read_only=True)

    class Meta:
        model = Referral
        fields = [
            'id', 'affiliate', 'affiliate_name', 'affiliate_code', 'customer_name', 'customer_email',
            'status', 'purchase_amount', 'referred_at'
        ]
        read_only_fields = ['id', 'affiliate', 'referred_at']

    def get_affiliate_name(self, obj):
        return obj.affiliate.full_name


class CommissionSerializer(serializers.ModelSerializer):
    affiliate_name = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source='referral.customer_name', read_only=True)
    customer_email = serializers.EmailField(source='referral.customer_email', read_only=True)

    class Meta:
        model = Commission
        fields = [
            'id', 'referral', 'affiliate', 'affiliate_name', 'customer_name', 'customer_email', 'amount',
            'status', 'payment_date', 'created_at'
        ]
        read_only_fields = ['id', 'affiliate', 'created_at']

    def get_affiliate_name(self, obj):
        return obj.affiliate.full_name


class PaymentSerializer(serializers.ModelSerializer):
    affiliate_name = serializers.SerializerMethodField()
    affiliate_code = serializers.CharField(source='affiliate.referral_code', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'affiliate', 'affiliate_name', 'affiliate_code', 'amount', 'payment_method',
            'transaction_id', 'status', 'paid_at'
        ]
        read_only_fields = ['id', 'affiliate', 'paid_at']

    def get_affiliate_name(self, obj):
        return obj.affiliate.full_name


class AffiliateNotificationSerializer(serializers.ModelSerializer):
    affiliate_name = serializers.SerializerMethodField()

    class Meta:
        model = AffiliateNotification
        fields = ['id', 'affiliate', 'affiliate_name', 'type', 'message', 'is_read', 'created_at']
        read_only_fields = ['id', 'affiliate', 'created_at']

    def get_affiliate_name(self, obj):
        return obj.affiliate.full_name
