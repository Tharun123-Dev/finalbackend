# utils/urls.py
from django.urls import path
from .views import (PermissionListView, AllRolesPermissionsView, UpdateRolePermissionsView, PermissionListView,
    AllRolesPermissionsView,
    UpdateRolePermissionsView,
    UserPermissionsView,
    CustomRoleListView,
    CustomRoleDetailView,)

urlpatterns = [
    path('permissions/',                          PermissionListView.as_view()),
    path('permissions/roles/',                    AllRolesPermissionsView.as_view()),
    path('permissions/roles/<str:role>/update/',  UpdateRolePermissionsView.as_view()),
       path('permissions/',                      PermissionListView.as_view()),
    path('permissions/roles/',                AllRolesPermissionsView.as_view()),
    path('permissions/roles/<str:role>/',     UpdateRolePermissionsView.as_view()),
    path('permissions/user/<int:user_id>/',   UserPermissionsView.as_view()),
    path('roles/custom/',                     CustomRoleListView.as_view()),
    path('roles/custom/<int:pk>/',            CustomRoleDetailView.as_view()),
]