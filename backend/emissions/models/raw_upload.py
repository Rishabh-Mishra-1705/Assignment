import uuid
from django.db import models
from django.contrib.auth.models import User
from .data_source import DataSource


class ProcessingStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    SUCCESS = 'SUCCESS', 'Success'
    PARTIAL = 'PARTIAL', 'Partial (some rows failed)'
    FAILED = 'FAILED', 'Failed'


class RawUpload(models.Model):
    """
    Stores every file upload event. We NEVER delete or overwrite raw files —
    auditors require the original artifact to exist.

    The raw file is stored as-is in /media/uploads/. We only parse it
    into EmissionRecords; we don't mutate the stored file.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(DataSource, on_delete=models.PROTECT, related_name='uploads')
    raw_file = models.FileField(upload_to='uploads/')
    original_filename = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64, blank=True)     # SHA-256 for dedup
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING
    )
    total_rows = models.IntegerField(default=0)
    success_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    error_log = models.JSONField(default=list, blank=True)      # Per-row errors

    def __str__(self):
        return f"{self.original_filename} @ {self.uploaded_at:%Y-%m-%d %H:%M}"

    class Meta:
        ordering = ['-uploaded_at']