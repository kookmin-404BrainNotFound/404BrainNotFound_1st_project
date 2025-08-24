from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (ContractViewSet,
                     StartContractView, AnalyzeContractView, ContractDataViewSet,
                     ContractByUserListView)

router = DefaultRouter()
router.register('', ContractViewSet, basename='image')
router.register('contractData', ContractDataViewSet, 'contract_data')

urlpatterns = [
    path("startContract/<int:user_id>", StartContractView.as_view(), name="start_contract"),
    path("<int:contract_id>/analyzeContract/", AnalyzeContractView.as_view(), name="analyze_contract"),
    path("getContractByUserId/<int:user_id>", ContractByUserListView.as_view(), name="get_contract_by_user"),
]

urlpatterns += router.urls
