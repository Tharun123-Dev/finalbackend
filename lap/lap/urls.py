# lap/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/',                    admin.site.urls),
    path('api/',                      include('employees.urls')),
    path('api/',                      include('leave.urls')),
    path('api/',                      include('attendance.urls')),
    path('api/',                      include('payroll.urls')),
    path('api/',                     include('reports.urls')),
    path('api/',                     include('notifications.urls')),
    path('api/',                     include('support_tickets.urls')),
    path('api/',                      include('affiliate.urls')),
     path('api/',                      include('leads.urls')), 
    path('api/',                      include('tasks.urls')),

    # Backward-compatible routes for frontends that call module paths directly
    # instead of using the /api prefix.
    path('',                           include('employees.urls')),
    path('',                           include('leave.urls')),
    path('',                           include('attendance.urls')),
    path('',                           include('payroll.urls')),
    path('',                           include('reports.urls')),
    path('',                           include('notifications.urls')),
    path('',                           include('support_tickets.urls')),
    path('',                           include('affiliate.urls')),
    path('',                           include('leads.urls')),
    path('',                           include('tasks.urls')),
]
