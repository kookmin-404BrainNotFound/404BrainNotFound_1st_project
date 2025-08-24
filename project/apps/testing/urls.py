# project/apps/testing/urls.py
from django.urls import path, include
from .views import FloodDepthProxyView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("flood-depth/", FloodDepthProxyView.as_view(), name="testing-flood-depth"),
    ]
