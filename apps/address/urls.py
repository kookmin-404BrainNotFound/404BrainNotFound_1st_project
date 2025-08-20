from django.urls import path
from .views import AddressSearchView, GetPriceView, GetPropertyRegistryView, GetBuildingInfoView

urlpatterns = [
    path("search/", AddressSearchView.as_view(), name="search"),
    path("price/", GetPriceView.as_view(), name="price"),
    path("property-registry/", GetPropertyRegistryView.as_view(), name="property_registry"),
    path("building-info/", GetBuildingInfoView.as_view(), name="building_info"),
]



