# project/apps/testing/urls.py
from django.urls import path, include
from .views import FloodDepthProxyView

urlpatterns = [
    path("flood-depth/", FloodDepthProxyView.as_view(), name="testing-flood-depth"),
]
