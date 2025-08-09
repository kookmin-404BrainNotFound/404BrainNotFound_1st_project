from django.urls import path
from .views import VWorldSearchView

urlpatterns = [
    path("search/", VWorldSearchView.as_view(), name="search"),
]



