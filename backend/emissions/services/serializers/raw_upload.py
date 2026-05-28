from rest_framework import serializers
from ...models import RawUpload


class RawUploadSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source='source.source_name', read_only=True)
    source_type = serializers.CharField(source='source.source_type', read_only=True)
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)

    class Meta:
        model = RawUpload
        fields = [
            'id', 'original_filename', 'uploaded_at', 'processing_status',
            'total_rows', 'success_rows', 'failed_rows', 'error_log',
            'source_name', 'source_type', 'uploaded_by_username',
        ]