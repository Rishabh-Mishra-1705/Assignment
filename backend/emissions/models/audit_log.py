import uuid
from django.db import models
from django.contrib.auth.models import User
from .emission_record import EmissionRecord


class AuditAction(models.TextChoices):
    CREATED = 'CREATED', 'Record Created'
    UPDATED = 'UPDATED', 'Record Updated'
    APPROVED = 'APPROVED', 'Record Approved'
    REJECTED = 'REJECTED', 'Record Rejected'
    LOCKED = 'LOCKED', 'Record Locked for Audit'
    FLAG_CHANGED = 'FLAG_CHANGED', 'Suspicious Flag Changed'


class AuditLog(models.Model):
    """
    Immutable append-only log. Every state change on an EmissionRecord
    creates an entry here.

    This is CRITICAL for ESG auditing: regulators need to see the full
    history of every data point, including who changed what and when.

    We use JSON fields for old/new values so we can store any field diff
    without schema changes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey(EmissionRecord, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=AuditAction.choices)
    field_name = models.CharField(max_length=100, blank=True)   # Which field changed
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)                         # Analyst's comment

    def __str__(self):
        return f"{self.action} on {self.record_id} @ {self.timestamp:%Y-%m-%d %H:%M}"

    class Meta:
        ordering = ['-timestamp']
        # AuditLogs are NEVER deleted or updated — read-only after creation
        default_permissions = ('add', 'view')