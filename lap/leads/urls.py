from django.urls import path
from . import views

urlpatterns = [
    # Forms
    path('leads/forms/', views.LeadFormListCreateView.as_view(), name='lead-form-list-create'),
    path('leads/forms/<int:form_id>/fields/', views.LeadFormFieldSyncView.as_view(), name='lead-form-fields-sync'),
    path('leads/forms/fields/', views.LeadFieldListCreateView.as_view(), name='lead-field-create'),
    path('leads/forms/fields/<int:field_id>/', views.LeadFieldDetailView.as_view(), name='lead-field-detail'),
    path('leads/options/', views.LeadOptionListSaveView.as_view(), name='lead-options'),

    # Leads
    path('leads/', views.LeadListCreateView.as_view(), name='lead-list-create'),
    path('leads/<int:lead_id>/', views.LeadDetailView.as_view(), name='lead-detail'),
    path('leads/<int:lead_id>/assign/<int:counselor_id>/', views.LeadAssignCounselorView.as_view(), name='lead-assign'),

    # FollowUps
    path('leads/followups/', views.FollowUpListCreateView.as_view(), name='followup-list-create'),
    path('leads/followups/<int:followup_id>/', views.FollowUpDetailView.as_view(), name='followup-detail'),

    # Analytics
    path('leads/analytics/dashboard/', views.LeadDashboardAnalyticsView.as_view(), name='lead-analytics'),
    path('revenue/overview/', views.RevenueOverviewView.as_view(), name='revenue-overview'),

    # Users for dropdowns
    path('leads/users/', views.LeadUsersListView.as_view(), name='lead-users'),
]
