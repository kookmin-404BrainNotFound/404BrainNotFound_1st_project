from django.urls import path
from .views import AddressSearchView, GetPriceView

urlpatterns = [
    path("search/", AddressSearchView.as_view(), name="search"),
    path("price/", GetPriceView.as_view(), name="price"),
]



