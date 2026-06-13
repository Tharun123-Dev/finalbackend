# accounts/urls.py — complete replacement
from django.urls import path
from .views import (
    CreateUserView, ListUsersView, MeView, UpdateUserView,
    UpdateProfileView, ChangePasswordView,
)

urlpatterns = [
    path('users/',                 ListUsersView.as_view()),
    path('users/create/',          CreateUserView.as_view()),
    path('users/me/',              MeView.as_view()),
    path('users/profile/',         UpdateProfileView.as_view()),
    path('users/change-password/', ChangePasswordView.as_view()),
    path('users/<int:pk>/',        UpdateUserView.as_view()),
]