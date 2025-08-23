from django.urls import path
from .views import AddressSearchView, GetPriceView, GetPropertyRegistryView, GetBuildingInfoView
from rest_framework.routers import DefaultRouter

urlpatterns = [
    path("search/", AddressSearchView.as_view(), name="search"),
    path("getPrice/", GetPriceView.as_view(), name="get_price"),
    path("getPropertyRegistry/", GetPropertyRegistryView.as_view(), name="get_property_registry"),
    path("getBuildingInfo/", GetBuildingInfoView.as_view(), name="get_building_info"),
]
