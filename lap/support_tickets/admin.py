from django.contrib import admin

from .models import SupportTicket, SupportTicketNote, SupportTicketType


@admin.register(SupportTicketType)
class SupportTicketTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'tenant_id', 'is_active')
    list_filter = ('tenant_id', 'is_active')
    search_fields = ('name', 'code')


class SupportTicketNoteInline(admin.TabularInline):
    model = SupportTicketNote
    extra = 0
    readonly_fields = ('author', 'created_at')


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_no', 'subject', 'tenant_id', 'priority', 'status', 'requester')
    list_filter = ('tenant_id', 'priority', 'status', 'issue_type')
    search_fields = ('ticket_no', 'subject', 'requester__username')
    inlines = [SupportTicketNoteInline]
