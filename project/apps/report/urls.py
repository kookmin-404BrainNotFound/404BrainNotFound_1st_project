from .views import StartReportView, SaveUserPriceView, MakeBuildingInfoReportView, MakeReportFinalView, MakeAvgPriceReportView
from django.urls import path

urlpatterns = [
    path('startReport/', StartReportView.as_view(), name='start_report'),
    path('<int:report_id>/saveUserPrice/', SaveUserPriceView.as_view(), name='save_user_price'),
    path('<int:report_id>/makeBuildingInfoReport/', MakeBuildingInfoReportView.as_view(), name='make_building_info_report'),
    path('<int:report_id>/makeAvgPriceReport/', MakeAvgPriceReportView.as_view(), name='make_avg_price_report'),
    path('<int:report_id>/makeReport/', MakeReportFinalView.as_view(), name='make_report'),
]

