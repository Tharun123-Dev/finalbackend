from django.contrib import admin
from .models import ReportLog
@admin.register(ReportLog)
class ReportLogAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'format', 'generated_by', 'created_at']