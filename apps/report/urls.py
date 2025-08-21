from .views import StartReportView, SavePriceView, MakeReportView
from django.urls import path

urlpatterns = [
    path('startReport/', StartReportView.as_view(), name='start_report'),
    path('savePrice/', SavePriceView.as_view(), name='save_price'),
    path('makeReport/', MakeReportView.as_view(), name='make_report'),
]

