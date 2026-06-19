# accounts/urls.py — complete replacement
from django.urls import path
from .views import (
    CreateUserView, ListUsersView, MeView, UpdateUserView,
    UpdateProfileView, ChangePasswordView, SupervisorOptionsView,
    UserHierarchyView, UserManagersView, ManagerHrsView,
    HrEmployeesView, TeamMembersView,
)

urlpatterns = [
    path('users/',                 ListUsersView.as_view()),
    path('users/create/',          CreateUserView.as_view()),
    path('users/supervisors/',     SupervisorOptionsView.as_view()),
    path('users/hierarchy/',       UserHierarchyView.as_view()),
    path('users/managers/',        UserManagersView.as_view()),
    path('users/manager/<str:manager_id>/hrs/', ManagerHrsView.as_view()),
    path('users/hr/<str:hr_id>/employees/', HrEmployeesView.as_view()),
    path('users/<str:user_id>/team-members/', TeamMembersView.as_view()),
    path('users/me/',              MeView.as_view()),
    path('users/profile/',         UpdateProfileView.as_view()),
    path('users/change-password/', ChangePasswordView.as_view()),
    path('users/<int:pk>/',        UpdateUserView.as_view()),
]
