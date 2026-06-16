# employees/views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from utils.permissions import make_permission, IsAuthenticatedUser
from accounts.tenant_utils import get_tenant_id
from accounts.models import User
from .models import Department, EmployeeProfile
from .access import employee_profile_visibility_q, role_group, visible_user_queryset
from .serializers import (
    DepartmentSerializer,
    EmployeeProfileSerializer,
    CreateEmployeeSerializer
)


# ─── DEPARTMENT VIEWS ────────────────────────────────────────────────────────

class DepartmentListCreateView(generics.ListCreateAPIView):
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        return Department.objects.filter(tenant_id=get_tenant_id(self.request))

    def get_permissions(self):
        if self.request.method == 'GET':
            return [make_permission('view_departments')()]
        return [make_permission('create_department')()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, tenant_id=get_tenant_id(self.request))


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        return Department.objects.filter(tenant_id=get_tenant_id(self.request))

    def get_permissions(self):
        if self.request.method == 'GET':
            return [make_permission('view_departments')()]
        if self.request.method == 'DELETE':
            return [make_permission('delete_department')()]
        return [make_permission('edit_department')()]


# ─── EMPLOYEE VIEWS ───────────────────────────────────────────────────────────

class EmployeeListView(generics.ListAPIView):
    serializer_class  = EmployeeProfileSerializer
    permission_classes = [make_permission('view_employees')]

    def get_queryset(self):
        qs = EmployeeProfile.objects.select_related(
            'user', 'department', 'manager'
        ).filter(
            user__tenant_id=get_tenant_id(self.request),
        ).filter(employee_profile_visibility_q(self.request))
        dept   = self.request.query_params.get('department')
        role   = self.request.query_params.get('role')
        active = self.request.query_params.get('active')
        search = self.request.query_params.get('search')

        if dept:
            qs = qs.filter(department_id=dept)
        if role:
            qs = qs.filter(user__role=role)
        if active is not None:
            qs = qs.filter(user__is_active=active.lower() == 'true')
        if search:
            qs = qs.filter(
                user__first_name__icontains=search
            ) | qs.filter(
                user__last_name__icontains=search
            ) | qs.filter(
                emp_code__icontains=search
            ) | qs.filter(
                user__email__icontains=search
            )
        return qs


class HrmsFiltersView(APIView):
    permission_classes = [make_permission('view_employees')]

    def get(self, request):
        users = visible_user_queryset(request, include_self=False).select_related('profile', 'custom_role')
        groups = {
            'admins': [],
            'hr': [],
            'managers': [],
            'team_leads': [],
            'employees': [],
        }
        roles = {}

        for user in users:
            profile = getattr(user, 'profile', None)
            item = {
                'id': user.id,
                'user_id': user.id,
                'name': user.get_full_name() or user.username,
                'username': user.username,
                'role': user.get_display_role(),
                'base_role': user.get_effective_role(),
                'manager': getattr(profile, 'manager_id', None),
                'designation': getattr(profile, 'designation', None),
                'emp_code': getattr(profile, 'emp_code', ''),
            }
            group = role_group(user)
            if group == 'admin':
                groups['admins'].append(item)
            elif group == 'hr':
                groups['hr'].append(item)
            elif group == 'manager':
                groups['managers'].append(item)
            elif group == 'team_lead':
                groups['team_leads'].append(item)
            else:
                groups['employees'].append(item)

            roles[item['role']] = {
                'label': item['role'],
                'base_role': item['base_role'],
            }

        return Response({
            'roles': list(roles.values()),
            'groups': groups,
        })


class CreateEmployeeView(APIView):
    permission_classes = [make_permission('create_employee')]

    def post(self, request):
        serializer = CreateEmployeeSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(created_by=request.user)
            profile = get_object_or_404(
                EmployeeProfile.objects.select_related('user', 'department', 'manager'),
                user=user,
            )
            return Response(
                {
                    'message': 'Employee created successfully',
                    'user_id': user.id,
                    'employee_id': profile.id,
                    'employee': EmployeeProfileSerializer(profile).data,
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeeDetailView(APIView):
    permission_classes = [make_permission('view_employees')]

    def get(self, request, pk):
        profile = get_object_or_404(
            EmployeeProfile.objects.select_related('user', 'department', 'manager'),
            pk=pk,
            user__tenant_id=get_tenant_id(request),
            user_id__in=visible_user_queryset(request).values('id'),
        )
        return Response(EmployeeProfileSerializer(profile).data)


class UpdateEmployeeView(APIView):
    permission_classes = [make_permission('edit_employee')]

    def patch(self, request, pk):
        profile = get_object_or_404(
            EmployeeProfile,
            pk=pk,
            user__tenant_id=get_tenant_id(request),
            user_id__in=visible_user_queryset(request).values('id'),
        )
        user    = profile.user

        # Update User fields if provided
        user_fields = ['first_name', 'last_name', 'email', 'role', 'employee_type']
        for field in user_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
        if 'is_active' in request.data:
            user.is_active = request.data['is_active']
        user.save()

        # Update Profile fields if provided
        profile_fields = [
            'designation', 'work_mode', 'department', 'phone', 'address',
            'manager', 'bank_account', 'ifsc_code', 'pan_number',
            'is_on_probation', 'date_of_birth', 'joining_date'
        ]
        for field in profile_fields:
            if field in request.data:
                if field == 'department':
                    profile.department_id = request.data[field]
                elif field == 'manager':
                    profile.manager_id = request.data[field]
                else:
                    setattr(profile, field, request.data[field])
        profile.save()

        updated = EmployeeProfile.objects.select_related(
            'user', 'department', 'manager'
        ).get(pk=pk, user__tenant_id=get_tenant_id(request))
        return Response(EmployeeProfileSerializer(updated).data)


class DeactivateEmployeeView(APIView):
    permission_classes = [make_permission('delete_employee')]

    def post(self, request, pk):
        profile = get_object_or_404(
            EmployeeProfile,
            pk=pk,
            user__tenant_id=get_tenant_id(request),
            user_id__in=visible_user_queryset(request).values('id'),
        )
        profile.user.is_active = False
        profile.user.save()
        return Response({'message': f'{profile.emp_code} deactivated successfully'})


class ManagerListView(APIView):
    """Returns list of managers/HR for dropdown in forms."""
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        managers = visible_user_queryset(request).filter(
            role__in=['manager', 'hr', 'admin', 'superadmin'],
        ).values('id', 'username', 'first_name', 'last_name', 'role')
        return Response(list(managers))
