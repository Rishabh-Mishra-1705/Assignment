from rest_framework import serializers
from ...models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'action', 'action_display', 'field_name',
            'old_value', 'new_value', 'changed_by_username', 'timestamp', 'note',
        ]