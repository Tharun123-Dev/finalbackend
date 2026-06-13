from django.db import models
from django.conf import settings

class ReportLog(models.Model):
    report_type  = models.CharField(max_length=30)
    format       = models.CharField(max_length=10, default='csv')
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    parameters   = models.JSONField(default=dict)
    created_at   = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f"{self.report_type} at {self.created_at}"