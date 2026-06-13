from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from accounts.tenant_utils import get_tenant_id
from utils.permissions import IsAuthenticatedUser, make_any_permission, make_permission
from .models import Task, TaskActivity, TaskComment, TaskNotification
from .serializers import TaskNotificationSerializer, TaskSerializer, TaskUserSerializer


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'dashboard', 'members', 'notifications']:
            return [make_any_permission('view_tasks', 'view_team_tasks', 'assign_task')()]
        if self.action == 'create':
            return [make_permission('create_task')()]
        if self.action in ['destroy']:
            return [make_permission('delete_task')()]
        return [make_any_permission('edit_task', 'assign_task')()]

    def get_queryset(self):
        user = self.request.user
        tenant_id = get_tenant_id(self.request)
        qs = Task.objects.select_related('assigned_to', 'assigned_by').prefetch_related(
            'comments__author', 'history__user'
        ).filter(tenant_id=tenant_id)

        if user.has_perm_code('view_team_tasks') or user.has_perm_code('assign_task'):
            return qs

        return qs.filter(Q(assigned_to=user) | Q(assigned_by=user))

    def perform_create(self, serializer):
        task = serializer.save(
            tenant_id=get_tenant_id(self.request),
            assigned_by=self.request.user,
        )
        TaskActivity.objects.create(
            task=task,
            user=self.request.user,
            action='Task Created',
            details=f'Task created and assigned to {task.assigned_to.get_full_name() or task.assigned_to.username if task.assigned_to else "Unassigned"}',
        )
        if task.assigned_to and task.assigned_to != self.request.user:
            TaskNotification.objects.create(
                tenant_id=task.tenant_id,
                recipient=task.assigned_to,
                sender=self.request.user,
                task=task,
                type='assigned',
                message=f'assigned you a task: {task.title}',
            )

    def perform_update(self, serializer):
        previous = self.get_object()
        old_status = previous.status
        old_assignee_id = previous.assigned_to_id
        task = serializer.save()

        if old_status != task.status:
            TaskActivity.objects.create(
                task=task,
                user=self.request.user,
                action='Status Updated',
                details=f'Changed status from {old_status} to {task.status}',
            )

        if old_assignee_id != task.assigned_to_id:
            TaskActivity.objects.create(
                task=task,
                user=self.request.user,
                action='Assignment Changed',
                details=f'Reassigned task to {task.assigned_to.get_full_name() or task.assigned_to.username if task.assigned_to else "Unassigned"}',
            )
            if task.assigned_to:
                TaskNotification.objects.create(
                    tenant_id=task.tenant_id,
                    recipient=task.assigned_to,
                    sender=self.request.user,
                    task=task,
                    type='assigned',
                    message=f'assigned you a task: {task.title}',
                )

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        task = self.get_object()
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'detail': 'Comment is required'}, status=status.HTTP_400_BAD_REQUEST)
        TaskComment.objects.create(task=task, author=request.user, content=content)
        TaskActivity.objects.create(task=task, user=request.user, action='Comment Added', details='Added a discussion comment')
        return Response(TaskSerializer(task, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        task = self.get_object()
        task.archived = True
        task.save(update_fields=['archived'])
        TaskActivity.objects.create(task=task, user=request.user, action='Task Archived', details='Archived task')
        return Response(TaskSerializer(task, context={'request': request}).data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedUser])
    def members(self, request):
        users = User.objects.filter(tenant_id=get_tenant_id(request), is_active=True).order_by('first_name', 'username')
        return Response(TaskUserSerializer(users, many=True).data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedUser])
    def notifications(self, request):
        notifications = TaskNotification.objects.filter(
            tenant_id=get_tenant_id(request),
            recipient=request.user,
        )
        return Response(TaskNotificationSerializer(notifications, many=True).data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticatedUser])
    def mark_notifications_read(self, request):
        TaskNotification.objects.filter(
            tenant_id=get_tenant_id(request),
            recipient=request.user,
        ).update(read=True)
        return Response({'message': 'Task notifications marked read'})
