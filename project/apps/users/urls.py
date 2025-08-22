from rest_framework.routers import DefaultRouter

from django.urls import path
from .views import RegisterView, LoginView, UserViewSet, UserTendencyView, ListAllTendenciesView

router = DefaultRouter()
router.register('', UserViewSet, basename='users')

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path("<int:user_id>/tendency/", UserTendencyView.as_view(), name="user-tendency"),
    path("tendencies/", ListAllTendenciesView.as_view(), name="list-all-tendencies"),
]

urlpatterns += router.urls
