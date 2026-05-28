from django.contrib import admin
from .models import Organization, DataSource, RawUpload, EmissionRecord, AuditLog


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['source_name', 'source_type', 'organization', 'ingestion_method']
    list_filter = ['source_type']


@admin.register(RawUpload)
class RawUploadAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'processing_status', 'total_rows', 'success_rows', 'uploaded_at']
    list_filter = ['processing_status']
    readonly_fields = ['file_hash', 'error_log']


@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    list_display = ['activity_type', 'scope', 'normalized_quantity', 'normalized_unit',
                    'activity_date', 'status', 'suspicious_flag', 'locked_for_audit']
    list_filter = ['scope', 'status', 'suspicious_flag', 'locked_for_audit', 'activity_type']
    search_fields = ['description', 'location', 'reference_id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'approved_by', 'approved_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'field_name', 'changed_by', 'timestamp']
    list_filter = ['action']
    readonly_fields = ['id', 'record', 'action', 'old_value', 'new_value', 'changed_by', 'timestamp']

    def has_add_permission(self, request):
        return False  # Audit logs are only created programmatically

    def has_change_permission(self, request, obj=None):
        return False  # Immutable