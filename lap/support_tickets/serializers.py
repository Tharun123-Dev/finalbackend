from rest_framework import serializers

from .models import SupportTicket, SupportTicketNote, SupportTicketType


class SupportTicketTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicketType
        fields = [
            'id', 'tenant_id', 'name', 'code', 'description',
            'is_active', 'created_at',
        ]
        read_only_fields = ['tenant_id', 'created_at']


class SupportTicketNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicketNote
        fields = [
            'id', 'author', 'author_name', 'note', 'status_from',
            'status_to', 'is_internal', 'created_at',
        ]
        read_only_fields = [
            'author', 'author_name', 'status_from', 'status_to', 'created_at',
        ]

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username


class SupportTicketSerializer(serializers.ModelSerializer):
    issue_type_name = serializers.CharField(source='issue_type.name', read_only=True)
    requester_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    resolved_by_name = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            'id', 'tenant_id', 'ticket_no', 'issue_type', 'issue_type_name',
            'requester', 'requester_name', 'subject', 'description',
            'priority', 'status', 'assigned_to', 'assigned_to_name',
            'resolved_by', 'resolved_by_name', 'resolution_note',
            'created_at', 'updated_at', 'resolved_at', 'closed_at', 'notes',
        ]
        read_only_fields = [
            'tenant_id', 'ticket_no', 'requester', 'requester_name',
            'assigned_to_name', 'resolved_by', 'resolved_by_name',
            'resolution_note', 'status', 'created_at', 'updated_at',
            'resolved_at', 'closed_at', 'notes',
        ]

    def get_requester_name(self, obj):
        return obj.requester.get_full_name() or obj.requester.username

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.username
        return None

    def get_resolved_by_name(self, obj):
        if obj.resolved_by:
            return obj.resolved_by.get_full_name() or obj.resolved_by.username
        return None

    def get_notes(self, obj):
        request = self.context.get('request')
        can_manage = bool(
            request and request.user and request.user.has_perm_code('manage_support_tickets')
        )
        notes = obj.notes.all()
        if not can_manage:
            notes = notes.filter(is_internal=False)
        return SupportTicketNoteSerializer(notes, many=True).data
