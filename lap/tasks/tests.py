from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User
from utils.models import Permission, UserPermissionOverride
from .models import Task


class TaskPermissionsTestCase(APITestCase):
    def setUp(self):
        # Create permissions
        self.perm_view_tasks, _ = Permission.objects.get_or_create(code='view_tasks', label='View Own Tasks', module='tasks')
        self.perm_view_team, _ = Permission.objects.get_or_create(code='view_team_tasks', label='View Team Tasks', module='tasks')
        self.perm_assign, _ = Permission.objects.get_or_create(code='assign_task', label='Assign Tasks', module='tasks')
        self.perm_edit, _ = Permission.objects.get_or_create(code='edit_task', label='Edit Tasks', module='tasks')
        self.perm_create, _ = Permission.objects.get_or_create(code='create_task', label='Create Tasks', module='tasks')

        # Create tenant and users
        self.tenant_id = 'test-tenant'
        
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='password123',
            tenant_id=self.tenant_id,
            role='manager'
        )
        # Grant manager permission to view team tasks and assign tasks
        UserPermissionOverride.objects.create(user=self.manager, permission=self.perm_view_team, is_granted=True)
        UserPermissionOverride.objects.create(user=self.manager, permission=self.perm_assign, is_granted=True)
        UserPermissionOverride.objects.create(user=self.manager, permission=self.perm_edit, is_granted=True)

        self.employee1 = User.objects.create_user(
            username='employee1',
            email='emp1@example.com',
            password='password123',
            tenant_id=self.tenant_id,
            role='employee'
        )
        # Grant employee1 view_tasks permission
        UserPermissionOverride.objects.create(user=self.employee1, permission=self.perm_view_tasks, is_granted=True)

        self.employee2 = User.objects.create_user(
            username='employee2',
            email='emp2@example.com',
            password='password123',
            tenant_id=self.tenant_id,
            role='employee'
        )
        UserPermissionOverride.objects.create(user=self.employee2, permission=self.perm_view_tasks, is_granted=True)

        # Create tasks
        self.task1 = Task.objects.create(
            title='Task for Employee 1',
            description='Test description 1',
            assigned_to=self.employee1,
            assigned_by=self.manager,
            tenant_id=self.tenant_id,
            status='pending'
        )
        self.task2 = Task.objects.create(
            title='Task for Employee 2',
            description='Test description 2',
            assigned_to=self.employee2,
            assigned_by=self.manager,
            tenant_id=self.tenant_id,
            status='pending'
        )

    def test_manager_sees_all_tasks(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.get(reverse('tasks-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Manager should see both tasks
        task_ids = [t['id'] for t in response.data]
        self.assertIn(self.task1.id, task_ids)
        self.assertIn(self.task2.id, task_ids)

    def test_employee_sees_only_assigned_tasks(self):
        self.client.force_authenticate(user=self.employee1)
        response = self.client.get(reverse('tasks-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Employee 1 should only see task 1
        task_ids = [t['id'] for t in response.data]
        self.assertIn(self.task1.id, task_ids)
        self.assertNotIn(self.task2.id, task_ids)

    def test_employee_cannot_retrieve_unassigned_task(self):
        self.client.force_authenticate(user=self.employee1)
        response = self.client.get(reverse('tasks-detail', args=[self.task2.id]))
        # Because of get_queryset filtering, it should return 404 (or 403)
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

    def test_employee_can_retrieve_assigned_task(self):
        self.client.force_authenticate(user=self.employee1)
        response = self.client.get(reverse('tasks-detail', args=[self.task1.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Task for Employee 1')

    def test_employee_can_update_assigned_task(self):
        self.client.force_authenticate(user=self.employee1)
        data = {'status': 'inProgress'}
        response = self.client.patch(reverse('tasks-detail', args=[self.task1.id]), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.status, 'inProgress')

    def test_employee_cannot_update_unassigned_task(self):
        self.client.force_authenticate(user=self.employee1)
        data = {'status': 'completed'}
        response = self.client.patch(reverse('tasks-detail', args=[self.task2.id]), data=data)
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

    def test_employee_can_comment_assigned_task(self):
        self.client.force_authenticate(user=self.employee1)
        response = self.client.post(reverse('tasks-comment', args=[self.task1.id]), data={'content': 'Working on this.'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.task1.comments.count(), 1)
        self.assertEqual(self.task1.comments.first().content, 'Working on this.')

    def test_employee_cannot_comment_unassigned_task(self):
        self.client.force_authenticate(user=self.employee1)
        response = self.client.post(reverse('tasks-comment', args=[self.task2.id]), data={'content': 'Attempting edit.'})
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])
