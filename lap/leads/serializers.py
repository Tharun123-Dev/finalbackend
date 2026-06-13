from rest_framework import serializers
from .models import Lead, LeadForm, LeadField, LeadFieldValue, FollowUp, LeadNotification, LeadOption
from django.contrib.auth import get_user_model

User = get_user_model()


# ─── User (minimal) ───────────────────────────────────────────────────────────

class CounselorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'role']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


# ─── LeadField ────────────────────────────────────────────────────────────────

class LeadFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadField
        fields = [
            'id', 'form', 'label', 'field_type', 'required',
            'placeholder', 'section', 'validation', 'is_core',
            'options', 'order'
        ]
        read_only_fields = ['id', 'form']


class LeadFieldCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadField
        fields = [
            'label', 'field_type', 'required', 'placeholder',
            'section', 'validation', 'is_core', 'options', 'order'
        ]


# ─── LeadForm ─────────────────────────────────────────────────────────────────

class LeadFormSerializer(serializers.ModelSerializer):
    fields = LeadFieldSerializer(many=True, read_only=True)

    class Meta:
        model = LeadForm
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'fields']
        read_only_fields = ['id', 'created_at']


class LeadFormCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadForm
        fields = ['name', 'description', 'is_active']


class LeadOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadOption
        fields = [
            'id', 'tenant_id', 'category', 'label', 'value',
            'color', 'sort_order', 'is_active', 'is_system'
        ]
        read_only_fields = ['id', 'tenant_id', 'is_system']


class LeadOptionCreateUpdateSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=['status', 'contact_method'])
    label = serializers.CharField(max_length=100)
    value = serializers.CharField(max_length=100, required=False, allow_blank=True)
    color = serializers.CharField(max_length=30, required=False, allow_blank=True)
    sort_order = serializers.IntegerField(required=False, default=0)
    is_active = serializers.BooleanField(required=False, default=True)


# ─── FieldSync ────────────────────────────────────────────────────────────────

class FieldSyncItemSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_null=True)
    label = serializers.CharField()
    field_type = serializers.ChoiceField(choices=[ft[0] for ft in LeadField._meta.get_field('field_type').choices])
    required = serializers.BooleanField(default=False)
    placeholder = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    section = serializers.CharField(required=False, default='General Details')
    validation = serializers.DictField(required=False, allow_null=True)
    is_core = serializers.BooleanField(required=False, default=False)
    options = serializers.ListField(
        child=serializers.CharField(), required=False, allow_null=True
    )
    order = serializers.IntegerField(default=0)


class FormFieldsSyncSerializer(serializers.Serializer):
    fields = FieldSyncItemSerializer(many=True)


# ─── LeadFieldValue ───────────────────────────────────────────────────────────

class LeadFieldValueSerializer(serializers.ModelSerializer):
    field = LeadFieldSerializer(read_only=True)

    class Meta:
        model = LeadFieldValue
        fields = ['id', 'lead', 'field_id', 'field', 'value']
        read_only_fields = ['id', 'lead']


class LeadFieldValueCreateSerializer(serializers.Serializer):
    field_id = serializers.IntegerField()
    value = serializers.CharField(allow_blank=True)


# ─── Lead ─────────────────────────────────────────────────────────────────────

class LeadSerializer(serializers.ModelSerializer):
    counselor = CounselorSerializer(read_only=True)
    field_values = LeadFieldValueSerializer(many=True, read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'full_name', 'email', 'phone', 'status',
            'revenue_amount', 'payment_status', 'payment_reference',
            'counselor', 'counselor_id', 'form_id', 'tenant_id',
            'created_at', 'updated_at', 'field_values'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'counselor']


class LeadCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    status = serializers.CharField(required=False, default='New')
    counselor_id = serializers.IntegerField(required=False, allow_null=True)
    revenue_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    payment_status = serializers.CharField(required=False, allow_blank=True)
    payment_reference = serializers.CharField(required=False, allow_blank=True)
    form_id = serializers.IntegerField(required=False, allow_null=True)
    dynamic_fields = LeadFieldValueCreateSerializer(many=True, required=False, default=[])


class LeadUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    status = serializers.CharField(required=False)
    counselor_id = serializers.IntegerField(required=False, allow_null=True)
    revenue_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    payment_status = serializers.CharField(required=False, allow_blank=True)
    payment_reference = serializers.CharField(required=False, allow_blank=True)
    form_id = serializers.IntegerField(required=False, allow_null=True)
    dynamic_fields = LeadFieldValueCreateSerializer(many=True, required=False)


# ─── FollowUp ─────────────────────────────────────────────────────────────────

class FollowUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowUp
        fields = [
            'id', 'lead_id', 'counselor_id', 'note',
            'scheduled_at', 'completed', 'created_at'
        ]
        read_only_fields = ['id', 'counselor_id', 'created_at']


class FollowUpCreateSerializer(serializers.Serializer):
    lead_id = serializers.IntegerField()
    note = serializers.CharField()
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
    completed = serializers.BooleanField(default=False)


class FollowUpUpdateSerializer(serializers.Serializer):
    note = serializers.CharField(required=False)
    scheduled_at = serializers.DateTimeField(required=False)
    completed = serializers.BooleanField(required=False)


# ─── Analytics ────────────────────────────────────────────────────────────────

class CounselorPerformanceSerializer(serializers.Serializer):
    name = serializers.CharField()
    total_assigned = serializers.IntegerField()
    confirmed = serializers.IntegerField()
    performance_ratio = serializers.FloatField()


class DashboardAnalyticsSerializer(serializers.Serializer):
    total_leads = serializers.IntegerField()
    status_distribution = serializers.DictField()
    conversion_rate = serializers.FloatField()
    counselor_performance = CounselorPerformanceSerializer(many=True)
