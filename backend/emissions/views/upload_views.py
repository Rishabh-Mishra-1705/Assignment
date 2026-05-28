"""
Upload Views
============
Handles file ingestion for all three source types.
Follows the pipeline: parse → normalize → validate → save → log
"""

import hashlib
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User

from ..models import Organization, DataSource, RawUpload, EmissionRecord, AuditLog
from ..models.raw_upload import ProcessingStatus
from ..models.audit_log import AuditAction
from ..models.data_source import SourceType
from ..services.serializers.raw_upload import RawUploadSerializer
from ..services.parsers.sap_parser import parse_sap_csv
from ..services.parsers.utility_parser import parse_utility_csv
from ..services.parsers.travel_parser import parse_travel_csv


def _get_or_create_defaults():
    """
    Returns (org, analyst_user) — creates defaults if they don't exist.
    In a real system, these come from the authenticated request.
    """
    org, _ = Organization.objects.get_or_create(name='Breathe ESG Demo', slug='breathe-esg-demo')
    user, _ = User.objects.get_or_create(
        username='analyst',
        defaults={'email': 'analyst@breathe.esg', 'is_staff': True}
    )
    if not user.has_usable_password():
        user.set_password('analyst123')
        user.save()
    return org, user


def _compute_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def _ingest_file(request, source_type_value: str, parser_fn):
    """
    Shared ingestion logic for all three source types.
    """
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided. Use multipart/form-data with key "file".'}, status=400)

    uploaded_file = request.FILES['file']
    file_bytes = uploaded_file.read()
    file_hash = _compute_file_hash(file_bytes)

    org, user = _get_or_create_defaults()

    # Get or create the data source
    source, _ = DataSource.objects.get_or_create(
        organization=org,
        source_type=source_type_value,
        defaults={'source_name': f"{source_type_value} Import", 'ingestion_method': 'CSV'}
    )

    # ── Duplicate detection ────────────────────────────────────────────────────
    if RawUpload.objects.filter(file_hash=file_hash).exists():
        return Response({'error': 'This file has already been uploaded (duplicate detected by hash).'}, status=409)

    # ── Create upload record ───────────────────────────────────────────────────
    raw_upload = RawUpload.objects.create(
        source=source,
        raw_file=uploaded_file,
        original_filename=uploaded_file.name,
        file_hash=file_hash,
        uploaded_by=user,
        processing_status=ProcessingStatus.PROCESSING,
    )

    # ── Parse ──────────────────────────────────────────────────────────────────
    try:
        records_data, errors = parser_fn(file_bytes)
    except Exception as e:
        raw_upload.processing_status = ProcessingStatus.FAILED
        raw_upload.error_log = [{'row': 0, 'error': str(e)}]
        raw_upload.save()
        return Response({'error': f'Parsing failed: {str(e)}'}, status=422)

    # ── Save records ───────────────────────────────────────────────────────────
    saved_records = []
    for rec_data in records_data:
        try:
            rec = EmissionRecord.objects.create(
                organization=org,
                source=source,
                upload=raw_upload,
                **rec_data,
            )
            # Create initial audit log entry
            AuditLog.objects.create(
                record=rec,
                action=AuditAction.CREATED,
                new_value={'status': rec.status, 'suspicious_flag': rec.suspicious_flag},
                changed_by=user,
                note=f'Ingested from {uploaded_file.name}',
            )
            saved_records.append(rec)
        except Exception as e:
            errors.append({'row': rec_data.get('row_number', '?'), 'error': str(e)})

    # ── Update upload summary ──────────────────────────────────────────────────
    raw_upload.total_rows = len(records_data) + len(errors)
    raw_upload.success_rows = len(saved_records)
    raw_upload.failed_rows = len(errors)
    raw_upload.error_log = errors
    raw_upload.processing_status = (
        ProcessingStatus.SUCCESS if not errors else
        ProcessingStatus.PARTIAL if saved_records else
        ProcessingStatus.FAILED
    )
    raw_upload.save()

    return Response({
        'upload_id': str(raw_upload.id),
        'filename': uploaded_file.name,
        'total_rows': raw_upload.total_rows,
        'success_rows': raw_upload.success_rows,
        'failed_rows': raw_upload.failed_rows,
        'processing_status': raw_upload.processing_status,
        'errors': errors[:20],   # Return first 20 errors to avoid huge response
    }, status=201)


class SAPUploadView(APIView):
    def post(self, request):
        return _ingest_file(request, SourceType.SAP, parse_sap_csv)


class UtilityUploadView(APIView):
    def post(self, request):
        return _ingest_file(request, SourceType.UTILITY, parse_utility_csv)


class TravelUploadView(APIView):
    def post(self, request):
        return _ingest_file(request, SourceType.TRAVEL, parse_travel_csv)


class UploadHistoryView(APIView):
    def get(self, request):
        uploads = RawUpload.objects.select_related('source').order_by('-uploaded_at')[:100]
        serializer = RawUploadSerializer(uploads, many=True)
        return Response(serializer.data)