"""
Review Views
============
Analyst workflow: browse, approve, reject, flag, and lock records.
Every state-change creates an AuditLog entry.
"""

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend

from ..models import EmissionRecord, AuditLog, Organization
from ..models.audit_log import AuditAction
from ..models.emission_record import RecordStatus
from ..services.serializers.emission_record import (
    EmissionRecordSerializer,
    EmissionRecordListSerializer
)


def _get_default_user():
    from django.contrib.auth.models import User
    user, _ = User.objects.get_or_create(username='analyst')
    return user


def _get_default_org():
    org, _ = Organization.objects.get_or_create(name='Breathe ESG Demo', slug='breathe-esg-demo')
    return org


class EmissionRecordListView(ListAPIView):
    """
    GET /api/records/?status=PENDING&scope=SCOPE_1&suspicious_flag=true
    """
    serializer_class = EmissionRecordListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'scope', 'activity_type', 'suspicious_flag', 'locked_for_audit']

    def get_queryset(self):
        org = _get_default_org()
        return EmissionRecord.objects.filter(organization=org).select_related('source', 'upload')


class EmissionRecordDetailView(RetrieveUpdateAPIView):
    """
    GET /api/records/<id>/       → full record + audit history
    PATCH /api/records/<id>/     → update editable fields (creates AuditLog)
    """
    serializer_class = EmissionRecordSerializer
    queryset = EmissionRecord.objects.all()

    def perform_update(self, serializer):
        instance = self.get_object()
        old_values = {
            field: getattr(instance, field)
            for field in serializer.validated_data
        }
        updated = serializer.save()
        user = _get_default_user()

        # Log each changed field separately for granular auditability
        for field, old_val in old_values.items():
            new_val = getattr(updated, field)
            if old_val != new_val:
                AuditLog.objects.create(
                    record=updated,
                    action=AuditAction.UPDATED,
                    field_name=field,
                    old_value=str(old_val),
                    new_value=str(new_val),
                    changed_by=user,
                )


class ApproveRecordView(APIView):
    """POST /api/records/<pk>/approve/"""
    def post(self, request, pk):
        try:
            record = EmissionRecord.objects.get(pk=pk)
        except EmissionRecord.DoesNotExist:
            return Response({'error': 'Record not found'}, status=404)

        if record.locked_for_audit:
            return Response({'error': 'Record is locked for audit.'}, status=400)
        if record.status == RecordStatus.APPROVED:
            return Response({'error': 'Already approved.'}, status=400)

        user = _get_default_user()
        record.status = RecordStatus.APPROVED
        record.approved_by = user
        record.approved_at = timezone.now()
        record.save()

        AuditLog.objects.create(
            record=record,
            action=AuditAction.APPROVED,
            new_value={'status': 'APPROVED'},
            changed_by=user,
            note=request.data.get('note', ''),
        )
        return Response({'status': 'approved', 'approved_at': record.approved_at})


class RejectRecordView(APIView):
    """POST /api/records/<pk>/reject/"""
    def post(self, request, pk):
        try:
            record = EmissionRecord.objects.get(pk=pk)
        except EmissionRecord.DoesNotExist:
            return Response({'error': 'Record not found'}, status=404)

        if record.locked_for_audit:
            return Response({'error': 'Record is locked for audit.'}, status=400)

        reason = request.data.get('reason', '')
        user = _get_default_user()
        record.status = RecordStatus.REJECTED
        record.rejection_reason = reason
        record.save()

        AuditLog.objects.create(
            record=record,
            action=AuditAction.REJECTED,
            new_value={'status': 'REJECTED', 'reason': reason},
            changed_by=user,
        )
        return Response({'status': 'rejected'})


class LockRecordView(APIView):
    """POST /api/records/<pk>/lock/ — locks record for audit, irreversible."""
    def post(self, request, pk):
        try:
            record = EmissionRecord.objects.get(pk=pk)
        except EmissionRecord.DoesNotExist:
            return Response({'error': 'Record not found'}, status=404)

        if record.status != RecordStatus.APPROVED:
            return Response({'error': 'Only approved records can be locked.'}, status=400)
        if record.locked_for_audit:
            return Response({'error': 'Already locked.'}, status=400)

        user = _get_default_user()
        record.locked_for_audit = True
        record.save()

        AuditLog.objects.create(
            record=record,
            action=AuditAction.LOCKED,
            new_value={'locked_for_audit': True},
            changed_by=user,
        )
        return Response({'status': 'locked'})


class BulkApproveView(APIView):
    """POST /api/records/bulk-approve/ → body: {ids: [...]}"""
    def post(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'No IDs provided'}, status=400)

        user = _get_default_user()
        updated = 0
        for pk in ids:
            try:
                record = EmissionRecord.objects.get(pk=pk)
                if not record.locked_for_audit and record.status == RecordStatus.PENDING:
                    record.status = RecordStatus.APPROVED
                    record.approved_by = user
                    record.approved_at = timezone.now()
                    record.save()
                    AuditLog.objects.create(
                        record=record, action=AuditAction.APPROVED,
                        new_value={'status': 'APPROVED'}, changed_by=user,
                        note='Bulk approval'
                    )
                    updated += 1
            except EmissionRecord.DoesNotExist:
                pass

        return Response({'approved': updated})