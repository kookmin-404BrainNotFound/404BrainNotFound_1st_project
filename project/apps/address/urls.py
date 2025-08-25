from django.urls import path
from .views import (AddressSearchView, GetPriceView,
                    GetPropertyRegistryView, GetBuildingInfoView,
                    UserPriceViewSet, BuildingInfoViewSet, AvgPriceViewSet,
                    PropertyRegistryViewSet, AirConditionViewSet, PropertyBundleViewSet,
                    FloodViewSet)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("user_price", UserPriceViewSet)
router.register("building_info", BuildingInfoViewSet)
router.register("avg_price", AvgPriceViewSet)
router.register("property_registry", PropertyRegistryViewSet)
router.register("air_condition", AirConditionViewSet)
router.register("flood", FloodViewSet)
router.register("property_bundle", PropertyBundleViewSet)

urlpatterns = [
    path("search/", AddressSearchView.as_view(), name="search"),
    path("getPrice/", GetPriceView.as_view(), name="get_price"),
    path("getPropertyRegistry/", GetPropertyRegistryView.as_view(), name="get_property_registry"),
    path("getBuildingInfo/", GetBuildingInfoView.as_view(), name="get_building_info"),
]

urlpatterns += router.urls