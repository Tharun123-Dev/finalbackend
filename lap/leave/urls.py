# leave/urls.py — FULL REPLACEMENT (adds carry-forward endpoint)
from django.urls import path
from .views import (
    LeaveTypeListCreateView, LeaveTypeDetailView,
    MyLeaveBalanceView, InitBalanceView, CarryForwardView,
    ApplyLeaveView, MyLeaveRequestsView, CancelLeaveView,
    AllLeaveRequestsView, LeaveActionView,
    LeavePriorUsageView, LeavePolicySettingsView,DeleteLeaveTypeView
)

urlpatterns = [
    path('leave/types/',                LeaveTypeListCreateView.as_view()),
    path('leave/types/<int:pk>/',       LeaveTypeDetailView.as_view()),
    path('leave/balance/',              MyLeaveBalanceView.as_view()),
    path('leave/balance/init/',         InitBalanceView.as_view()),
    path('leave/carry-forward/',        CarryForwardView.as_view()),
    path('leave/apply/',                ApplyLeaveView.as_view()),
    path('leave/my/',                   MyLeaveRequestsView.as_view()),
    path('leave/<int:pk>/cancel/',      CancelLeaveView.as_view()),
    path('leave/all/',                  AllLeaveRequestsView.as_view()),
    path('leave/<int:pk>/action/',      LeaveActionView.as_view()),
    path('leave/<int:pk>/prior-usage/', LeavePriorUsageView.as_view()),
    path('leave/policy-settings/',      LeavePolicySettingsView.as_view()),  # NEW — system settings sync
    path(
    'leave/types/<int:pk>/',
    DeleteLeaveTypeView.as_view()
),
]