from rest_framework import serializers
from ...models import EmissionRecord, AuditLog


class EmissionRecordListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views (table rows)."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)

    class Meta:
        model = EmissionRecord
        fields = [
            'id', 'scope', 'scope_display', 'activity_type', 'activity_type_display',
            'normalized_quantity', 'normalized_unit', 'estimated_emission_kgco2e',
            'activity_date', 'status', 'status_display', 'suspicious_flag',
            'location', 'supplier', 'locked_for_audit', 'created_at',
        ]


class EmissionRecordSerializer(serializers.ModelSerializer):
    """Full serializer for detail/update views."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    audit_logs = serializers.SerializerMethodField()

    class Meta:
        model = EmissionRecord
        fields = '__all__'
        read_only_fields = [
            'id', 'organization', 'source', 'upload', 'row_number',
            'quantity', 'unit', 'raw_date',             # Never change raw data
            'normalized_quantity', 'normalized_unit',   # Normalizer owns these
            'emission_factor', 'estimated_emission_kgco2e',
            'approved_by', 'approved_at', 'locked_for_audit',
            'created_at', 'updated_at',
        ]

    def get_audit_logs(self, obj):
        logs = obj.audit_logs.all()[:10]  # Last 10 events
        return AuditLogSerializer(logs, many=True).data

    def validate(self, data):
        # Prevent editing locked records
        if self.instance and self.instance.locked_for_audit:
            raise serializers.ValidationError("This record is locked for audit and cannot be modified.")
        return data