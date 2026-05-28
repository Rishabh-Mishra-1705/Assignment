import uuid
from django.db import models
from django.contrib.auth.models import User
from .organization import Organization
from .data_source import DataSource
from .raw_upload import RawUpload


class EmissionScope(models.TextChoices):
    SCOPE_1 = 'SCOPE_1', 'Scope 1 — Direct'
    SCOPE_2 = 'SCOPE_2', 'Scope 2 — Purchased Electricity'
    SCOPE_3 = 'SCOPE_3', 'Scope 3 — Value Chain / Travel'


class ActivityType(models.TextChoices):
    # Scope 1
    DIESEL_COMBUSTION = 'DIESEL_COMBUSTION', 'Diesel Combustion'
    NATURAL_GAS = 'NATURAL_GAS', 'Natural Gas Combustion'
    FUEL_OIL = 'FUEL_OIL', 'Fuel Oil Combustion'
    # Scope 2
    ELECTRICITY_PURCHASED = 'ELECTRICITY_PURCHASED', 'Purchased Electricity'
    # Scope 3
    AIR_TRAVEL = 'AIR_TRAVEL', 'Air Travel'
    HOTEL_STAY = 'HOTEL_STAY', 'Hotel Stay'
    GROUND_TRANSPORT = 'GROUND_TRANSPORT', 'Ground Transport'
    PROCUREMENT = 'PROCUREMENT', 'Procurement / Supply Chain'


class RecordStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Review'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    NEEDS_REVIEW = 'NEEDS_REVIEW', 'Needs Manual Review'


class EmissionRecord(models.Model):
    """
    THE core model. A single normalized, immutable-after-approval row
    of emission activity data.

    Design decisions:
    - We store BOTH original (quantity/unit) AND normalized (normalized_quantity/
      normalized_unit) fields. This preserves the audit trail while enabling
      consistent calculations.
    - emission_factor is the kgCO2e per unit. We store it at ingest time so
      future factor updates don't silently change historical figures.
    - suspicious_flag is auto-set by validators but can be overridden by analysts.
    - locked_for_audit makes the row immutable; no edits allowed post-lock.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ── Lineage ────────────────────────────────────────────────────────────────
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name='records')
    source = models.ForeignKey(DataSource, on_delete=models.PROTECT, related_name='records')
    upload = models.ForeignKey(RawUpload, on_delete=models.PROTECT, related_name='records', null=True, blank=True)
    row_number = models.IntegerField(null=True, blank=True)     # Row in original CSV

    # ── Classification ─────────────────────────────────────────────────────────
    scope = models.CharField(max_length=10, choices=EmissionScope.choices)
    activity_type = models.CharField(max_length=30, choices=ActivityType.choices)
    category = models.CharField(max_length=100, blank=True)     # Free-text sub-category
    description = models.TextField(blank=True)

    # ── Raw (as received) ──────────────────────────────────────────────────────
    quantity = models.FloatField()
    unit = models.CharField(max_length=30)
    raw_date = models.CharField(max_length=50)                  # Original date string

    # ── Normalized ────────────────────────────────────────────────────────────
    normalized_quantity = models.FloatField()
    normalized_unit = models.CharField(max_length=30)           # Always liters or kWh
    activity_date = models.DateField()                          # Parsed, canonical date
    currency = models.CharField(max_length=10, blank=True)
    normalized_currency = models.CharField(max_length=10, blank=True, default='USD')
    cost_amount = models.FloatField(null=True, blank=True)

    # ── Emission Calculation ───────────────────────────────────────────────────
    emission_factor = models.FloatField(null=True, blank=True)  # kgCO2e / normalized_unit
    estimated_emission_kgco2e = models.FloatField(null=True, blank=True)

    # ── Additional Context ────────────────────────────────────────────────────
    location = models.CharField(max_length=255, blank=True)
    supplier = models.CharField(max_length=255, blank=True)
    reference_id = models.CharField(max_length=100, blank=True)  # SAP doc number, invoice ID

    # ── Workflow ───────────────────────────────────────────────────────────────
    status = models.CharField(max_length=15, choices=RecordStatus.choices, default=RecordStatus.PENDING)
    suspicious_flag = models.BooleanField(default=False)
    suspicious_reason = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_records'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    locked_for_audit = models.BooleanField(default=False)

    # ── Timestamps ─────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.activity_type} | {self.normalized_quantity} {self.normalized_unit} | {self.activity_date}"

    class Meta:
        ordering = ['-activity_date', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'scope']),
            models.Index(fields=['suspicious_flag']),
            models.Index(fields=['activity_date']),
        ]