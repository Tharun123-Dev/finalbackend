from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.utils import notify_permission, notify_user
from utils.permissions import IsAuthenticatedUser, make_any_permission, make_permission

from .models import SupportTicket, SupportTicketNote, SupportTicketType
from .serializers import SupportTicketSerializer, SupportTicketTypeSerializer
from .utils import get_tenant_id, seed_default_ticket_types


class SupportTicketTypeListCreateView(generics.ListCreateAPIView):
    serializer_class = SupportTicketTypeSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [make_any_permission('raise_support_ticket', 'view_support_tickets', 'manage_support_tickets')()]
        return [make_any_permission('manage_support_tickets', 'manage_support_ticket_types')()]

    def get_queryset(self):
        tenant_id = get_tenant_id(self.request)
        seed_default_ticket_types(tenant_id, self.request.user)
        return SupportTicketType.objects.filter(tenant_id=tenant_id, is_active=True)

    def perform_create(self, serializer):
        serializer.save(tenant_id=get_tenant_id(self.request), created_by=self.request.user)


class SupportTicketTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SupportTicketTypeSerializer
    permission_classes = [make_permission('manage_support_ticket_types')]

    def get_queryset(self):
        return SupportTicketType.objects.filter(tenant_id=get_tenant_id(self.request))

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])


class MySupportTicketsView(APIView):
    permission_classes = [make_permission('view_support_tickets')]

    def get(self, request):
        qs = SupportTicket.objects.filter(
            tenant_id=get_tenant_id(request), requester=request.user
        ).select_related('issue_type', 'requester', 'assigned_to', 'resolved_by').prefetch_related('notes')
        return Response(SupportTicketSerializer(qs, many=True, context={'request': request}).data)


class AllSupportTicketsView(APIView):
    permission_classes = [make_permission('manage_support_tickets')]

    def get(self, request):
        qs = SupportTicket.objects.filter(
            tenant_id=get_tenant_id(request)
        ).select_related('issue_type', 'requester', 'assigned_to', 'resolved_by').prefetch_related('notes')

        status_filter = request.query_params.get('status')
        priority = request.query_params.get('priority')
        issue_type = request.query_params.get('issue_type')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if priority:
            qs = qs.filter(priority=priority)
        if issue_type:
            qs = qs.filter(issue_type_id=issue_type)

        return Response(SupportTicketSerializer(qs, many=True, context={'request': request}).data)


class RaiseSupportTicketView(APIView):
    permission_classes = [make_permission('raise_support_ticket')]

    def post(self, request):
        tenant_id = get_tenant_id(request)
        seed_default_ticket_types(tenant_id, request.user)
        serializer = SupportTicketSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        issue_type = serializer.validated_data['issue_type']
        if issue_type.tenant_id != tenant_id or not issue_type.is_active:
            return Response({'error': 'Invalid issue type for this tenant'}, status=400)

        ticket = serializer.save(tenant_id=tenant_id, requester=request.user, status='open')
        SupportTicketNote.objects.create(
            ticket=ticket, author=request.user, note='Ticket raised', status_to='open'
        )
        notify_permission(
            'manage_support_tickets',
            title=f"Support Ticket Raised: {ticket.ticket_no}",
            body=f"{ticket.requester.get_full_name() or ticket.requester.username} raised {ticket.issue_type.name}: {ticket.subject}",
            notif_type='general',
            exclude_user=request.user,
        )
        notify_user(
            request.user,
            title=f"Ticket Submitted: {ticket.ticket_no}",
            body=f"Your {ticket.issue_type.name} ticket is open. Priority: {ticket.priority}.",
            notif_type='general',
        )
        return Response(SupportTicketSerializer(ticket, context={'request': request}).data, status=status.HTTP_201_CREATED)


class SupportTicketActionView(APIView):
    permission_classes = [make_permission('manage_support_tickets')]

    def post(self, request, pk):
        ticket = get_object_or_404(
            SupportTicket.objects.select_related('requester', 'issue_type'),
            pk=pk,
            tenant_id=get_tenant_id(request),
        )
        action = request.data.get('action')
        note = (request.data.get('note') or '').strip()
        is_internal = bool(request.data.get('is_internal', False))
        old_status = ticket.status

        if action not in ['assign', 'in_progress', 'waiting_user', 'resolve', 'close', 'reopen', 'note']:
            return Response({'error': 'Invalid action'}, status=400)
        if action in ['resolve', 'close', 'reopen', 'waiting_user', 'in_progress'] and not note:
            return Response({'error': 'note is required for this action'}, status=400)

        if action == 'assign':
            ticket.assigned_to = request.user
        elif action == 'in_progress':
            ticket.status = 'in_progress'
            ticket.assigned_to = ticket.assigned_to or request.user
        elif action == 'waiting_user':
            ticket.status = 'waiting_user'
        elif action == 'resolve':
            ticket.status = 'resolved'
            ticket.resolved_by = request.user
            ticket.resolution_note = note
            ticket.resolved_at = timezone.now()
        elif action == 'close':
            ticket.status = 'closed'
            ticket.closed_at = timezone.now()
        elif action == 'reopen':
            ticket.status = 'reopened'
            ticket.closed_at = None
            ticket.resolved_at = None

        ticket.save()
        SupportTicketNote.objects.create(
            ticket=ticket,
            author=request.user,
            note=note or f"Ticket {action.replace('_', ' ')}",
            status_from=old_status,
            status_to=ticket.status if old_status != ticket.status else '',
            is_internal=is_internal,
        )

        if not is_internal:
            notify_user(
                ticket.requester,
                title=f"Ticket Updated: {ticket.ticket_no}",
                body=f"Status: {ticket.status}. Note: {note or action.replace('_', ' ')}",
                notif_type='general',
            )
        return Response(SupportTicketSerializer(ticket, context={'request': request}).data)


class SupportTicketRequesterActionView(APIView):
    permission_classes = [make_permission('view_support_tickets')]

    def post(self, request, pk):
        return Response(
            {'error': 'Requester tracking is read-only. Only support managers can update tickets.'},
            status=status.HTTP_403_FORBIDDEN,
        )


class SupportTicketSummaryView(APIView):
    permission_classes = [make_any_permission('raise_support_ticket', 'view_support_tickets', 'manage_support_tickets')]

    def get(self, request):
        tenant_id = get_tenant_id(request)
        base = SupportTicket.objects.filter(tenant_id=tenant_id)
        mine = base.filter(requester=request.user)
        can_manage = request.user.has_perm_code('manage_support_tickets')
        qs = base if can_manage else mine
        return Response({
            'tenant_id': tenant_id,
            'scope': 'all' if can_manage else 'mine',
            'can_manage': can_manage,
            'total': qs.count(),
            'open': qs.filter(status='open').count(),
            'in_progress': qs.filter(status='in_progress').count(),
            'waiting_user': qs.filter(status='waiting_user').count(),
            'resolved': qs.filter(status='resolved').count(),
            'closed': qs.filter(status='closed').count(),
            'reopened': qs.filter(status='reopened').count(),
            'urgent': qs.filter(priority='urgent').count(),
        })
