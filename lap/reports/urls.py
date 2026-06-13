# reports/urls.py
from django.urls import path
from .views import (
    ReportsDashboardView,
    AttendanceReportView,
    LeaveReportView,
    PayrollReportView,
    HeadcountReportView,
    LopSummaryView,
    OvertimeReportView,
)

urlpatterns = [
    path('reports/dashboard/',  ReportsDashboardView.as_view()),
    path('reports/attendance/', AttendanceReportView.as_view()),
    path('reports/leave/',      LeaveReportView.as_view()),
    path('reports/payroll/',    PayrollReportView.as_view()),
    path('reports/headcount/',  HeadcountReportView.as_view()),
    path('reports/lop/',        LopSummaryView.as_view()),
    path('reports/overtime/',   OvertimeReportView.as_view()),
]