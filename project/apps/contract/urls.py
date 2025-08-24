from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContractViewSet, StartContractView

router = DefaultRouter()
router.register('', ContractViewSet, basename='image')

urlpatterns = [
    path("startContract/", StartContractView.as_view(), name="start_contract")
]


urlpatterns += router.urls
