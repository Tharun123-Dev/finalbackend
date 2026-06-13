# notifications/urls.py
from django.urls import path
from .views import (
    MyNotificationsView,
    MarkReadView,
    MarkAllReadView,
    UnreadCountView,
    DeleteNotificationView,
    SystemSettingsView,
    SystemSettingDetailView,
)

urlpatterns = [
    # Notifications
    path('notifications/',                  MyNotificationsView.as_view()),
    path('notifications/unread-count/',     UnreadCountView.as_view()),
    path('notifications/read-all/',         MarkAllReadView.as_view()),
    path('notifications/<int:pk>/read/',    MarkReadView.as_view()),
    path('notifications/<int:pk>/',         DeleteNotificationView.as_view()),

    # System Settings
    path('system-settings/',               SystemSettingsView.as_view()),
    path('system-settings/<str:key>/',     SystemSettingDetailView.as_view()),
]