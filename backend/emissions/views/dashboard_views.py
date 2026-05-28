"""
Dashboard Views
===============
Aggregated statistics for the analyst dashboard.
"""

from django.db.models import Count, Sum, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import EmissionRecord, RawUpload, Organization
from ..models.emission_record import RecordStatus, EmissionScope


def _get_default_org():
    org, _ = Organization.objects.get_or_create(name='Breathe ESG Demo', slug='breathe-esg-demo')
    return org


class DashboardStatsView(APIView):
    """GET /api/dashboard/stats/"""
    def get(self, request):
        org = _get_default_org()
        records = EmissionRecord.objects.filter(organization=org)

        stats = {
            'total_records': records.count(),
            'pending': records.filter(status=RecordStatus.PENDING).count(),
            'approved': records.filter(status=RecordStatus.APPROVED).count(),
            'rejected': records.filter(status=RecordStatus.REJECTED).count(),
            'suspicious': records.filter(suspicious_flag=True).count(),
            'locked': records.filter(locked_for_audit=True).count(),

            # CO2e totals by scope (only approved records)
            'scope1_kgco2e': records.filter(
                status=RecordStatus.APPROVED, scope=EmissionScope.SCOPE_1
            ).aggregate(t=Sum('estimated_emission_kgco2e'))['t'] or 0,

            'scope2_kgco2e': records.filter(
                status=RecordStatus.APPROVED, scope=EmissionScope.SCOPE_2
            ).aggregate(t=Sum('estimated_emission_kgco2e'))['t'] or 0,

            'scope3_kgco2e': records.filter(
                status=RecordStatus.APPROVED, scope=EmissionScope.SCOPE_3
            ).aggregate(t=Sum('estimated_emission_kgco2e'))['t'] or 0,

            'recent_uploads': RawUpload.objects.select_related('source').order_by('-uploaded_at').values(
                'id', 'original_filename', 'processing_status', 'success_rows',
                'failed_rows', 'uploaded_at'
            )[:5],
        }

        # Convert to tCO2e for display
        stats['total_tco2e'] = round(
            (stats['scope1_kgco2e'] + stats['scope2_kgco2e'] + stats['scope3_kgco2e']) / 1000, 2
        )
        stats['scope1_tco2e'] = round(stats['scope1_kgco2e'] / 1000, 2)
        stats['scope2_tco2e'] = round(stats['scope2_kgco2e'] / 1000, 2)
        stats['scope3_tco2e'] = round(stats['scope3_kgco2e'] / 1000, 2)

        return Response(stats)