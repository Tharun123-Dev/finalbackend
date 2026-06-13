# payroll/urls.py
from django.urls import path
from .views import (
    PayrollSettingsDefaultsView,
    SalaryStructureListView, CreateSalaryStructureView,
    UpdateSalaryStructureView, MySalaryStructureView,
    PayrollRunListView, CreatePayrollRunView,
    ProcessPayrollRunView, ApprovePayrollRunView,
    PayrollRunDetailView, UpdatePayrollEntryView,
    AddAdjustmentView, MyPayslipListView, MyPayslipDetailView,
    PayrollRegisterView,
    MyDeductionHistoryView, EmployeeDeductionHistoryView,
    AllDeductionSummaryView, DashboardStatsView,
)

urlpatterns = [
    # ── Payroll system settings defaults (for salary auto-fill)
    path('payroll/settings-defaults/',            PayrollSettingsDefaultsView.as_view()),

    # ── Salary structures — mine MUST be before <int:pk>
    path('payroll/salary/',                       SalaryStructureListView.as_view()),
    path('payroll/salary/create/',                CreateSalaryStructureView.as_view()),
    path('payroll/salary/mine/',                  MySalaryStructureView.as_view()),
    path('payroll/salary/<int:pk>/',              UpdateSalaryStructureView.as_view()),

    # ── Payroll runs
    path('payroll/runs/',                         PayrollRunListView.as_view()),
    path('payroll/runs/create/',                  CreatePayrollRunView.as_view()),
    path('payroll/runs/<int:pk>/',                PayrollRunDetailView.as_view()),
    path('payroll/runs/<int:pk>/process/',        ProcessPayrollRunView.as_view()),
    path('payroll/runs/<int:pk>/approve/',        ApprovePayrollRunView.as_view()),
    path('payroll/runs/<int:pk>/register/',       PayrollRegisterView.as_view()),

    # ── Entry level
    path('payroll/entries/<int:pk>/',              UpdatePayrollEntryView.as_view()),
    path('payroll/entries/<int:entry_pk>/adjust/', AddAdjustmentView.as_view()),

    # ── Payslips — mine before <int:month>
    path('payroll/payslips/',                          MyPayslipListView.as_view()),
    path('payroll/payslips/<int:month>/<int:year>/',   MyPayslipDetailView.as_view()),

    # ── Deduction history
    path('payroll/deductions/mine/',                       MyDeductionHistoryView.as_view()),
    path('payroll/deductions/employee/<int:emp_id>/',      EmployeeDeductionHistoryView.as_view()),
    path('payroll/deductions/summary/',                    AllDeductionSummaryView.as_view()),

    # ── Dashboard stats
    path('payroll/dashboard-stats/',                       DashboardStatsView.as_view()),
]