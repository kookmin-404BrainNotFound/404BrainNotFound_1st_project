from .views import (StartReportView, SaveUserPriceView, MakeBuildingInfoView, 
                    MakeReportFinalView, MakeAvgPriceView, MakePropertyRegistryView,
                    ReportDataListAllView, ReportDataByReportView, ReportListAllView, ReportListByUserView,
                    ReportDetailedSummaryView, MakeAirConditionView)
from django.urls import path

urlpatterns = [
    path('startReport/', StartReportView.as_view(), name='start_report'),
    path("reports/", ReportListAllView.as_view(), name="report-list-all"),
    path("users/<int:user_id>/reports/", ReportListByUserView.as_view(), name="report-list-by-user"),
    path("<int:report_id>/getReportSummary/", ReportDetailedSummaryView.as_view(), name="get_report_summary"),
    path('<int:report_id>/saveUserPrice/', SaveUserPriceView.as_view(), name='save_user_price'),
    path('<int:report_id>/makeBuildingInfo/', MakeBuildingInfoView.as_view(), name='make_building_info_report'),
    path('<int:report_id>/makeAvgPrice/', MakeAvgPriceView.as_view(), name='make_avg_price_report'),
    path('<int:report_id>/makePropertyRegistry/', MakePropertyRegistryView.as_view(), name='make_property_registry'),
    path('<int:report_id>/makeAirCondition/', MakeAirConditionView.as_view(), name='make_air_condition'),
    path('<int:report_id>/makeReport/', MakeReportFinalView.as_view(), name='make_report'),
    path("report_data/", ReportDataListAllView.as_view(), name="reportdata_list_all"),
    path("<int:report_id>/report_data/", ReportDataByReportView.as_view(), name="reportdata-by-report"),
]

