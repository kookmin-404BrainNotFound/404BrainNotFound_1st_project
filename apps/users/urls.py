from rest_framework.routers import DefaultRouter

from django.urls import path
from .views import RegisterView, LoginView, UserViewSet

router = DefaultRouter()
router.register('', UserViewSet, basename='users')

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
]

urlpatterns += router.urls
