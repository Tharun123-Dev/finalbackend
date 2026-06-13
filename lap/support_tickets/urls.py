from django.urls import path

from .views import (
    AllSupportTicketsView,
    MySupportTicketsView,
    RaiseSupportTicketView,
    SupportTicketActionView,
    SupportTicketRequesterActionView,
    SupportTicketSummaryView,
    SupportTicketTypeDetailView,
    SupportTicketTypeListCreateView,
)

urlpatterns = [
    path('support/ticket-types/', SupportTicketTypeListCreateView.as_view()),
    path('support/ticket-types/<int:pk>/', SupportTicketTypeDetailView.as_view()),
    path('support/tickets/raise/', RaiseSupportTicketView.as_view()),
    path('support/tickets/my/', MySupportTicketsView.as_view()),
    path('support/tickets/all/', AllSupportTicketsView.as_view()),
    path('support/tickets/summary/', SupportTicketSummaryView.as_view()),
    path('support/tickets/<int:pk>/action/', SupportTicketActionView.as_view()),
    path('support/tickets/<int:pk>/requester-action/', SupportTicketRequesterActionView.as_view()),
]
