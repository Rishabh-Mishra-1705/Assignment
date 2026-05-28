import uuid
from django.db import models
from .organization import Organization


class SourceType(models.TextChoices):
    SAP = 'SAP', 'SAP Fuel & Procurement'
    UTILITY = 'UTILITY', 'Utility Electricity'
    TRAVEL = 'TRAVEL', 'Corporate Travel'


class IngestionMethod(models.TextChoices):
    CSV = 'CSV', 'CSV File Upload'
    API = 'API', 'API Pull'
    MANUAL = 'MANUAL', 'Manual Entry'


class DataSource(models.Model):
    """
    Describes WHERE data originates. This enables analysts to filter
    records by system-of-origin and track which systems are unreliable.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='data_sources')
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    source_name = models.CharField(max_length=255)          # e.g. "SAP Plant DE01"
    ingestion_method = models.CharField(max_length=20, choices=IngestionMethod.choices, default=IngestionMethod.CSV)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source_name} ({self.source_type})"

    class Meta:
        unique_together = ('organization', 'source_name')