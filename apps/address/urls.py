from django.urls import path
from .views import VWorldSearchView, GetPriceView

urlpatterns = [
    path("search/", VWorldSearchView.as_view(), name="search"),
    path("price/", GetPriceView.as_view(), name="price"),
]



