from django.contrib import admin
from .models import Task, TaskActivity, TaskComment, TaskNotification

admin.site.register(Task)
admin.site.register(TaskComment)
admin.site.register(TaskActivity)
admin.site.register(TaskNotification)
