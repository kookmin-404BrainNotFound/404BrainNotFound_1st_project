"""
URL configuration for safehome project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including anotherfrom django.conf.urls.static import static URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import routers
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


router = routers.DefaultRouter()

schema_view = get_schema_view(
    openapi.Info(
        title="SafeHome API",
        default_version="v1",
        description="SafeHome description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes = [permissions.AllowAny],
    patterns=[
        path("testing/", include("apps.testing.urls")),
        path("user/", include("apps.users.urls")),
        path("address/", include("apps.address.urls")),
        path("gpt/", include("apps.gpt.urls")),
        path("report/", include("apps.report.urls")),
        path("api/", include("apps.image.urls")),
    ],
    url=settings.API_URL,
)

urlpatterns = [
    path('testing/', include('apps.testing.urls')),
    path('admin/', admin.site.urls),
    path('user/', include('apps.users.urls')),
    path('address/', include('apps.address.urls')),
    path('gpt/', include('apps.gpt.urls')),
    path('report/', include('apps.report.urls')),
    path('api/', include('apps.image.urls')),
]


urlpatterns += [
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',schema_view.without_ui(cache_timeout=0),name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0),name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0),name='schema-redoc'),
]

# 개발환경에서 미디어 파일 제공
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)