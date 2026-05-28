from django.urls import path
from .views.upload_views import SAPUploadView, UtilityUploadView, TravelUploadView, UploadHistoryView
from .views.review_views import (
    EmissionRecordListView, EmissionRecordDetailView,
    ApproveRecordView, RejectRecordView, LockRecordView, BulkApproveView
)
from .views.dashboard_views import DashboardStatsView

urlpatterns = [
    # ── Ingestion ─────────────────────────────────────────────────────────────
    path('upload/sap/',     SAPUploadView.as_view(),     name='upload-sap'),
    path('upload/utility/', UtilityUploadView.as_view(), name='upload-utility'),
    path('upload/travel/',  TravelUploadView.as_view(),  name='upload-travel'),
    path('uploads/',        UploadHistoryView.as_view(), name='upload-history'),

    # ── Records ───────────────────────────────────────────────────────────────
    path('records/',                         EmissionRecordListView.as_view(),   name='record-list'),
    path('records/<uuid:pk>/',               EmissionRecordDetailView.as_view(), name='record-detail'),
    path('records/<uuid:pk>/approve/',       ApproveRecordView.as_view(),        name='record-approve'),
    path('records/<uuid:pk>/reject/',        RejectRecordView.as_view(),         name='record-reject'),
    path('records/<uuid:pk>/lock/',          LockRecordView.as_view(),           name='record-lock'),
    path('records/bulk-approve/',            BulkApproveView.as_view(),          name='record-bulk-approve'),

    # ── Dashboard ─────────────────────────────────────────────────────────────
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]