from django.urls import path
from .views import AddressSearchView, GetPriceView, GetPropertyRegistryView

urlpatterns = [
    path("search/", AddressSearchView.as_view(), name="search"),
    path("price/", GetPriceView.as_view(), name="price"),
    path("property-registry/", GetPropertyRegistryView.as_view(), name="property_registry"),
]



