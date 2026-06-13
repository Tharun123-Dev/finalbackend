# affiliate/urls.py
from django.urls import path
from .views import (
    AffiliateRegisterView,
    AffiliateProfileView,
    ReferralListView,
    ReferralDetailView,
    RegisterCustomerView,
    CommissionListView,
    PaymentListView,
    PaymentProcessView,
    DashboardStatsView,
    ReferralGrowthView,
    EarningsPerformanceView,
    AffiliateNotificationListView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
)

urlpatterns = [
    # Auth
    path('affiliate/auth/register/',                   AffiliateRegisterView.as_view()),

    # Profile
    path('affiliate/profile/',                         AffiliateProfileView.as_view()),

    # Referrals
    path('affiliate/referrals/',                       ReferralListView.as_view()),
    path('affiliate/referrals/register-customer/',     RegisterCustomerView.as_view()),
    path('affiliate/referrals/<uuid:pk>/',             ReferralDetailView.as_view()),

    # Commissions
    path('affiliate/commissions/',                     CommissionListView.as_view()),

    # Payments
    path('affiliate/payments/',                        PaymentListView.as_view()),
    path('affiliate/payments/<uuid:pk>/process/',      PaymentProcessView.as_view()),

    # Analytics
    path('affiliate/analytics/dashboard-stats/',       DashboardStatsView.as_view()),
    path('affiliate/analytics/referral-growth/',       ReferralGrowthView.as_view()),
    path('affiliate/analytics/earnings-performance/',  EarningsPerformanceView.as_view()),

    # Notifications
    path('affiliate/notifications/',                   AffiliateNotificationListView.as_view()),
    path('affiliate/notifications/read-all/',          MarkAllNotificationsReadView.as_view()),
    path('affiliate/notifications/<uuid:pk>/read/',    MarkNotificationReadView.as_view()),
]
