# employees/urls.py
from django.urls import path
from .views import (
    DepartmentListCreateView, DepartmentDetailView,
    EmployeeListView, CreateEmployeeView,
    EmployeeDetailView, UpdateEmployeeView,
    DeactivateEmployeeView, ManagerListView,
)

urlpatterns = [
    # Departments
    path('departments/',        DepartmentListCreateView.as_view()),
    path('departments/<int:pk>/', DepartmentDetailView.as_view()),

    # Employees
    path('employees/',              EmployeeListView.as_view()),
    path('employees/create/',       CreateEmployeeView.as_view()),
    path('employees/managers/',     ManagerListView.as_view()),
    path('employees/<int:pk>/',     EmployeeDetailView.as_view()),
    path('employees/<int:pk>/update/', UpdateEmployeeView.as_view()),
    path('employees/<int:pk>/deactivate/', DeactivateEmployeeView.as_view()),
]