# employees/admin.py
from django.contrib import admin
from .models import Department, EmployeeProfile

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ['emp_code', 'user', 'department', 'designation', 'joining_date']
    search_fields = ['emp_code', 'user__first_name', 'user__last_name']