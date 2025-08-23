from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContractViewSet

router = DefaultRouter()
router.register('', ContractViewSet, basename='image')

urlpatterns = [
    path('', include(router.urls)),
]


# urlpatterns = [
#     path('upload/', upload_image, name="upload_image"),
# ]