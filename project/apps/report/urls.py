from .views import (StartReportView, SaveUserPriceView, MakeBuildingInfoView, 
                    MakeReportFinalView, MakeAvgPriceView, MakePropertyRegistryView, ReportListByUserView,
                    MakeAirConditionView, ReportDataViewSet, ReportViewSet, GetReportDataByReportIdView, MakeFloodView)
from django.urls import path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("", ReportViewSet)
router.register("report_data", ReportDataViewSet)

urlpatterns = [
    path('startReport/', StartReportView.as_view(), name='start_report'),
    path("users/<int:user_id>/", ReportListByUserView.as_view(), name="report-list-by-user"),
    path('<int:report_id>/saveUserPrice/', SaveUserPriceView.as_view(), name='save_user_price'),
    path('<int:report_id>/makeBuildingInfo/', MakeBuildingInfoView.as_view(), name='make_building_info_report'),
    path('<int:report_id>/makeAvgPrice/', MakeAvgPriceView.as_view(), name='make_avg_price_report'),
    path('<int:report_id>/makePropertyRegistry/', MakePropertyRegistryView.as_view(), name='make_property_registry'),
    path('<int:report_id>/makeAirCondition/', MakeAirConditionView.as_view(), name='make_air_condition'),
    path('<int:report_id>/makeFlood/', MakeFloodView.as_view(), name='make_flood'),
    path('<int:report_id>/makeReport/', MakeReportFinalView.as_view(), name='make_report'),
    path('getReportByReportId/<int:report_id>/', GetReportDataByReportIdView.as_view(), name="get_report_by_report_id"),
]

urlpatterns += router.urls

