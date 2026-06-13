# attendance/urls.py
# ── REPLACEMENT FILE ──
# Replace: Backend/lap/attendance/urls.py
# Change:  Adds  path('attendance/holidays/<int:pk>/',  HolidayDetailView)
#          for PUT/PATCH/DELETE on individual holidays.
from django.urls import path
from .views import (
    CheckInView, CheckOutView, TodayAttendanceView,
    MyAttendanceView, AllAttendanceView,
    ApplyRegularizationView, MyRegularizationsView,
    AllRegularizationsView, ApproveRegularizationView,
    HolidayListView, HolidayDetailView,
    OfficeLocationView,
)

urlpatterns = [
    # ── Core check-in / out ───────────────────────────────────────────────────
    path('attendance/checkin/',                       CheckInView.as_view()),
    path('attendance/checkout/',                      CheckOutView.as_view()),
    path('attendance/today/',                         TodayAttendanceView.as_view()),

    # ── Records ───────────────────────────────────────────────────────────────
    path('attendance/my/',                            MyAttendanceView.as_view()),
    path('attendance/all/',                           AllAttendanceView.as_view()),

    # ── Regularisation ────────────────────────────────────────────────────────
    path('attendance/regularize/',                    ApplyRegularizationView.as_view()),
    path('attendance/regularize/my/',                 MyRegularizationsView.as_view()),
    path('attendance/regularize/all/',                AllRegularizationsView.as_view()),
    path('attendance/regularize/<int:pk>/action/',    ApproveRegularizationView.as_view()),

    # ── Holidays (list/create + detail edit/delete) ───────────────────────────
    path('attendance/holidays/',                      HolidayListView.as_view()),
    path('attendance/holidays/<int:pk>/',             HolidayDetailView.as_view()),   # ← NEW

    # ── Office location ───────────────────────────────────────────────────────
    path('attendance/office-location/',               OfficeLocationView.as_view()),
]