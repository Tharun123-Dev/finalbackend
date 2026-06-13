# affiliate/views.py
from datetime import timedelta
from uuid import uuid4
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from utils.permissions import make_any_permission
from utils.models import Permission, UserPermissionOverride

from .models import (
    Affiliate, Referral, Commission, Payment,
    AffiliateNotification, generate_referral_code
)
from .serializers import (
    AffiliateProfileSerializer, AffiliateUpdateSerializer,
    AffiliateRegisterSerializer, ReferralSerializer,
    CommissionSerializer, PaymentSerializer, AffiliateNotificationSerializer,
)

AffiliateAccess = make_any_permission('view_affiliate', 'manage_affiliate')
AffiliateManageAccess = make_any_permission('manage_affiliate')


def affiliate_commission_rate():
    return float(getattr(settings, 'AFFILIATE_COMMISSION_RATE', 0.10))


def affiliate_min_payout():
    return float(getattr(settings, 'AFFILIATE_MIN_PAYOUT_AMOUNT', 500.0))


def affiliate_payment_mode():
    return getattr(settings, 'AFFILIATE_PAYMENT_MODE', 'manual')


def has_affiliate_manage(user):
    return bool(user and user.is_authenticated and user.has_perm_code('manage_affiliate'))


def has_affiliate_view(user):
    return bool(user and user.is_authenticated and user.has_perm_code('view_affiliate'))


def create_affiliate_profile(user):
    full_name = user.get_full_name() or user.username or user.email or 'Affiliate'
    code = generate_referral_code(full_name)
    while Affiliate.objects.filter(referral_code=code).exists():
        code = generate_referral_code(full_name)
    return Affiliate.objects.create(
        user=user,
        referral_code=code,
        profile_image_url=(
            f"https://ui-avatars.com/api/?name="
            f"{full_name.replace(' ', '+')}&background=random"
        ),
    )


def get_affiliate_or_404(request, create_if_missing=True):
    try:
        return request.user.affiliate_profile
    except Affiliate.DoesNotExist:
        if create_if_missing and (has_affiliate_view(request.user) or has_affiliate_manage(request.user)):
            return create_affiliate_profile(request.user)
        return None


def scoped_affiliate_queryset(request, model):
    if has_affiliate_manage(request.user):
        return model.objects.all()
    affiliate = get_affiliate_or_404(request)
    if not affiliate:
        return model.objects.none()
    return model.objects.filter(affiliate=affiliate)


# ─── AUTH ─────────────────────────────────────────────────────────────────────

class AffiliateRegisterView(APIView):
    """
    POST /api/affiliate/auth/register/
    Registers a new LAP user + creates their affiliate profile in one step.
    Login uses existing LAP endpoint: POST /api/auth/login/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        serializer = AffiliateRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        email = data['email']

        if User.objects.filter(email=email).exists():
            return Response(
                {'detail': 'A user with this email already exists.'},
                status=400
            )

        full_name = f"{data['first_name']} {data.get('last_name', '')}".strip()

        user = User.objects.create_user(
            username=email,
            email=email,
            password=data['password'],
            first_name=data['first_name'],
            last_name=data.get('last_name', ''),
            role='employee',
        )
        try:
            perm = Permission.objects.get(code='view_affiliate')
            UserPermissionOverride.objects.update_or_create(
                user=user,
                permission=perm,
                defaults={'is_granted': True, 'reason': 'Affiliate registration'},
            )
        except Permission.DoesNotExist:
            pass

        code = generate_referral_code(full_name)
        while Affiliate.objects.filter(referral_code=code).exists():
            code = generate_referral_code(full_name)

        affiliate = Affiliate.objects.create(
            user=user,
            referral_code=code,
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            bank_account_details=data.get('bank_account_details', ''),
            bank_name=data.get('bank_name', ''),
            account_number=data.get('account_number', ''),
            payout_method=data.get('payout_method', 'ACH/Direct Deposit'),
            upi_id=data.get('upi_id', ''),
            profile_image_url=(
                f"https://ui-avatars.com/api/?name="
                f"{full_name.replace(' ', '+')}&background=random"
            ),
        )

        return Response(
            AffiliateProfileSerializer(affiliate).data,
            status=status.HTTP_201_CREATED
        )


# ─── PROFILE ──────────────────────────────────────────────────────────────────

class AffiliateProfileView(APIView):
    """
    GET  /api/affiliate/profile/
    PUT  /api/affiliate/profile/
    PATCH /api/affiliate/profile/
    """
    permission_classes = [AffiliateAccess]

    def get(self, request):
        affiliate = get_affiliate_or_404(request)
        if not affiliate:
            return Response({'detail': 'Affiliate profile not found.'}, status=404)
        return Response(AffiliateProfileSerializer(affiliate).data)

    def put(self, request):
        affiliate = get_affiliate_or_404(request)
        if not affiliate:
            return Response({'detail': 'Affiliate profile not found.'}, status=404)
        serializer = AffiliateUpdateSerializer(affiliate, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(AffiliateProfileSerializer(affiliate).data)
        return Response(serializer.errors, status=400)

    def patch(self, request):
        return self.put(request)


# ─── REFERRALS ────────────────────────────────────────────────────────────────

class ReferralListView(APIView):
    """GET /api/affiliate/referrals/?status=pending&skip=0&limit=100"""
    permission_classes = [AffiliateAccess]

    def get(self, request):
        qs = scoped_affiliate_queryset(request, Referral)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        skip = int(request.query_params.get('skip', 0))
        limit = int(request.query_params.get('limit', 100))

        return Response(ReferralSerializer(qs[skip:skip + limit], many=True).data)


class ReferralDetailView(APIView):
    """GET /api/affiliate/referrals/<uuid:pk>/"""
    permission_classes = [AffiliateAccess]

    def get(self, request, pk):
        try:
            referral = scoped_affiliate_queryset(request, Referral).get(pk=pk)
        except Referral.DoesNotExist:
            return Response({'detail': 'Referral not found.'}, status=404)
        return Response(ReferralSerializer(referral).data)


class RegisterCustomerView(APIView):
    """
    POST /api/affiliate/referrals/register-customer/
    PUBLIC endpoint — called when a customer clicks a referral link.
    No auth required.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        referral_code = str(request.data.get('referral_code') or '').strip()
        customer_name = request.data.get('customer_name')
        customer_email = request.data.get('customer_email')
        product_name = request.data.get('product_name', '')
        purchase_amount = float(request.data.get('purchase_amount', 0.0))

        if not all([referral_code, customer_name, customer_email]):
            return Response(
                {'detail': 'referral_code, customer_name and customer_email are required.'},
                status=400
            )

        try:
            affiliate = Affiliate.objects.get(referral_code__iexact=referral_code)
        except Affiliate.DoesNotExist:
            return Response({'detail': 'Invalid referral code.'}, status=404)

        if Referral.objects.filter(customer_email=customer_email).exists():
            return Response({'detail': 'Customer email already registered.'}, status=400)

        ref_status = 'converted' if purchase_amount > 0.0 else 'pending'
        referral = Referral.objects.create(
            affiliate=affiliate,
            customer_name=customer_name,
            customer_email=customer_email,
            status=ref_status,
            purchase_amount=purchase_amount,
        )

        if purchase_amount > 0.0:
            commission_amount = round(purchase_amount * affiliate_commission_rate(), 2)
            Commission.objects.create(
                referral=referral,
                affiliate=affiliate,
                amount=commission_amount,
                status='pending',
            )
            affiliate.total_earnings += commission_amount
            affiliate.save(update_fields=['total_earnings'])

            AffiliateNotification.objects.create(
                affiliate=affiliate,
                type='referral',
                message=(
                    f"New Conversion! {customer_name} subscribed to {product_name}. "
                    f"Commission of ₹{commission_amount:.2f} credited."
                ),
            )
        else:
            AffiliateNotification.objects.create(
                affiliate=affiliate,
                type='referral',
                message=f"New Lead! {customer_name} registered using your referral link.",
            )

        return Response({'status': 'success', 'message': 'Customer registered successfully.'})


# ─── COMMISSIONS ──────────────────────────────────────────────────────────────

class CommissionListView(APIView):
    """GET /api/affiliate/commissions/?status=pending"""
    permission_classes = [AffiliateAccess]

    def get(self, request):
        qs = scoped_affiliate_queryset(request, Commission)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        skip = int(request.query_params.get('skip', 0))
        limit = int(request.query_params.get('limit', 100))

        return Response(CommissionSerializer(qs[skip:skip + limit], many=True).data)


# ─── PAYMENTS ─────────────────────────────────────────────────────────────────

class PaymentListView(APIView):
    """GET /api/affiliate/payments/"""
    permission_classes = [AffiliateAccess]

    def get(self, request):
        skip = int(request.query_params.get('skip', 0))
        limit = int(request.query_params.get('limit', 100))
        payments = scoped_affiliate_queryset(request, Payment)[skip:skip + limit]

        return Response(PaymentSerializer(payments, many=True).data)

    def post(self, request):
        affiliate = get_affiliate_or_404(request)
        if not affiliate:
            return Response({'detail': 'Affiliate profile not found.'}, status=404)

        amount = float(request.data.get('amount') or affiliate.pending_earnings or 0)
        if amount <= 0:
            return Response({'detail': 'Payout amount must be greater than zero.'}, status=400)
        if amount > affiliate.pending_earnings:
            return Response({'detail': 'Payout amount exceeds pending earnings.'}, status=400)

        minimum = affiliate_min_payout()
        if amount < minimum:
            return Response({'detail': f'Minimum payout amount is {minimum}.'}, status=400)

        payment = Payment.objects.create(
            affiliate=affiliate,
            amount=amount,
            payment_method=affiliate.payout_method or affiliate_payment_mode(),
            transaction_id=f"REQ-{uuid4().hex[:12].upper()}",
            status='processing',
        )
        AffiliateNotification.objects.create(
            affiliate=affiliate,
            type='payment',
            message=f"Payout request for {amount:.2f} has been submitted and is processing.",
        )
        return Response(PaymentSerializer(payment).data, status=201)


class PaymentProcessView(APIView):
    """PATCH /api/affiliate/payments/<uuid:pk>/process/ - admin/manual settlement."""
    permission_classes = [AffiliateManageAccess]

    def patch(self, request, pk):
        try:
            payment = Payment.objects.select_related('affiliate').get(pk=pk)
        except Payment.DoesNotExist:
            return Response({'detail': 'Payment not found.'}, status=404)

        next_status = request.data.get('status', 'completed')
        if next_status not in ('processing', 'completed', 'failed'):
            return Response({'detail': 'Invalid payment status.'}, status=400)

        payment.status = next_status
        if request.data.get('transaction_id'):
            payment.transaction_id = request.data['transaction_id']
        if request.data.get('payment_method'):
            payment.payment_method = request.data['payment_method']
        payment.save()

        affiliate = payment.affiliate
        if next_status == 'completed':
            affiliate.paid_earnings += payment.amount
            affiliate.save(update_fields=['paid_earnings'])
            remaining = payment.amount
            for commission in Commission.objects.filter(affiliate=affiliate, status='pending').order_by('created_at'):
                if remaining <= 0:
                    break
                commission.status = 'paid'
                commission.payment_date = timezone.now()
                commission.save(update_fields=['status', 'payment_date'])
                remaining -= commission.amount

        AffiliateNotification.objects.create(
            affiliate=affiliate,
            type='payment',
            message=f"Payout {payment.transaction_id} is now {next_status}.",
        )
        return Response(PaymentSerializer(payment).data)


# ─── ANALYTICS ────────────────────────────────────────────────────────────────

class DashboardStatsView(APIView):
    """GET /api/affiliate/analytics/dashboard-stats/"""
    permission_classes = [AffiliateAccess]

    def get(self, request):
        referral_qs = scoped_affiliate_queryset(request, Referral)
        commission_qs = scoped_affiliate_queryset(request, Commission)
        affiliate_qs = Affiliate.objects.all() if has_affiliate_manage(request.user) else Affiliate.objects.filter(pk=get_affiliate_or_404(request).pk)

        total_referrals = referral_qs.count()
        converted = referral_qs.filter(status='converted').count()
        conversion_rate = round((converted / total_referrals * 100), 2) if total_referrals > 0 else 0.0

        now = timezone.now()
        first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly = commission_qs.filter(
            created_at__gte=first_day
        ).aggregate(total=Sum('amount'))['total'] or 0.0
        total_earnings = affiliate_qs.aggregate(total=Sum('total_earnings'))['total'] or 0.0
        paid_earnings = affiliate_qs.aggregate(total=Sum('paid_earnings'))['total'] or 0.0
        total_clicks = affiliate_qs.aggregate(total=Sum('total_clicks'))['total'] or 0
        active_campaigns = affiliate_qs.aggregate(total=Sum('active_campaigns'))['total'] or 0

        return Response({
            'total_earnings': total_earnings,
            'pending_earnings': total_earnings - paid_earnings,
            'paid_earnings': paid_earnings,
            'total_clicks': total_clicks,
            'total_referrals': total_referrals,
            'conversion_rate': conversion_rate,
            'active_campaigns': active_campaigns,
            'this_month_earnings': monthly,
        })


class ReferralGrowthView(APIView):
    """GET /api/affiliate/analytics/referral-growth/ — last 7 days"""
    permission_classes = [AffiliateAccess]

    def get(self, request):
        referral_qs = scoped_affiliate_queryset(request, Referral)
        stats = []
        for i in range(6, -1, -1):
            day = (timezone.now() - timedelta(days=i)).date()
            count = referral_qs.filter(
                referred_at__date=day,
            ).count()
            stats.append({'date': day.strftime('%b %d'), 'referrals': count})
        return Response(stats)


class EarningsPerformanceView(APIView):
    """GET /api/affiliate/analytics/earnings-performance/ — last 6 months"""
    permission_classes = [AffiliateAccess]

    def get(self, request):
        commission_qs = scoped_affiliate_queryset(request, Commission)
        stats = []
        now = timezone.now()
        for i in range(5, -1, -1):
            month_date = now - timedelta(days=i * 30)
            amount = commission_qs.filter(
                created_at__month=month_date.month,
                created_at__year=month_date.year,
            ).aggregate(total=Sum('amount'))['total'] or 0.0
            stats.append({'month': month_date.strftime('%b'), 'earnings': amount})
        return Response(stats)


# ─── NOTIFICATIONS (affiliate-specific) ──────────────────────────────────────

class AffiliateNotificationListView(APIView):
    """GET /api/affiliate/notifications/"""
    permission_classes = [AffiliateAccess]

    def get(self, request):
        skip = int(request.query_params.get('skip', 0))
        limit = int(request.query_params.get('limit', 50))
        notifs = scoped_affiliate_queryset(request, AffiliateNotification)[skip:skip + limit]
        return Response(AffiliateNotificationSerializer(notifs, many=True).data)


class MarkNotificationReadView(APIView):
    """PUT /api/affiliate/notifications/<uuid:pk>/read/"""
    permission_classes = [AffiliateAccess]

    def put(self, request, pk):
        affiliate = get_affiliate_or_404(request)
        if not affiliate and not has_affiliate_manage(request.user):
            return Response({'detail': 'Affiliate profile not found.'}, status=404)
        try:
            qs = AffiliateNotification.objects.all() if has_affiliate_manage(request.user) else AffiliateNotification.objects.filter(affiliate=affiliate)
            notif = qs.get(pk=pk)
            notif.is_read = True
            notif.save(update_fields=['is_read'])
        except AffiliateNotification.DoesNotExist:
            return Response({'detail': 'Notification not found.'}, status=404)
        return Response({'msg': 'Marked as read'})


class MarkAllNotificationsReadView(APIView):
    """PUT /api/affiliate/notifications/read-all/"""
    permission_classes = [AffiliateAccess]

    def put(self, request):
        affiliate = get_affiliate_or_404(request)
        if not affiliate and not has_affiliate_manage(request.user):
            return Response({'detail': 'Affiliate profile not found.'}, status=404)
        qs = AffiliateNotification.objects.all() if has_affiliate_manage(request.user) else AffiliateNotification.objects.filter(affiliate=affiliate)
        qs.filter(is_read=False).update(is_read=True)
        return Response({'msg': 'All marked as read'})
