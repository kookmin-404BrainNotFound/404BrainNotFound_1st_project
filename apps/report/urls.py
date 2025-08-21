from .views import StartReportView, DangerCheckListView
from django.urls import path

urlpatterns = [
    path('startReport/', StartReportView.as_view(), name='start_report'),
    path('danger-checklist/<int:report_run_id>/', DangerCheckListView.as_view(), name='danger_checklist'),
]

