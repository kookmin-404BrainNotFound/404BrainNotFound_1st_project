import inspect

from rest_framework import viewsets, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
    OpenApiParameter, OpenApiTypes, inline_serializer,
)

from django.shortcuts import render
from io import BytesIO
from django.http import FileResponse

from external.client.business_juso import BusinessJusoClient
from external.client.seoul_data import DataSeoulClient
from external.address.building_info import BuildingInfoManager
from external.address.property_registry import get_property_registry

from external.address.address_manager import AddressManager
from .serializers import (AddressSearchSerializer, GetPriceSerializer,
                          GetPropertyRegistrySerializer, GetBuildingInfoSerializer, PropertyRegistrySerializer,
                          UserPriceSerializer, BuildingInfoSerializer, AvgPriceSerializer,
                          AirConditionSerializer, PropertyBundleSerializer,
                          FloodSerializer)
from .models import (UserPrice, BuildingInfo, AvgPrice, PropertyRegistry,
                     AirCondition, PropertyBundle, Flood)

# Create your views here.

class AddressSearchView(APIView):
    @extend_schema(
        summary="주소 검색",
        description="장소를 검색합니다.",
        parameters=[AddressSearchSerializer],
        tags=["address_apis"],
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        serializer = AddressSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        client = BusinessJusoClient()
        data = client.search_address(
            query = serializer.validated_data["q"],
            size=serializer.validated_data["size"],
            page=serializer.validated_data["page"],
        )
        client.close()

        return Response(data)

# 전월세가 가져오기 검색 API에서 파싱해서 다시 전달필요함.
class GetPriceView(APIView):
    @extend_schema(
        summary="전월세 가격 조회.",
        description="전월세 가격을 도로명 주소로 조회합니다.",
        parameters=[GetPriceSerializer],
        tags=["address_apis"],
    )
    def get(self, request):
        serializer = GetPriceSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        # road address로 검색 진행, Parsing
        address:AddressManager = AddressManager(roadAddr=vd["roadAddr"])
        address.initialize(research=True)

        if not address.is_valid():
            return Response({"error": "유효하지 않은 주소입니다."}, status=400)
        
        client = DataSeoulClient()
        
        data = client.getPrice(
            size = vd["size"],
            year = vd["year"],
            address = address,
        )
        client.close()
        
        return Response(data)

    
# 등기부등본 가져오기.
class GetPropertyRegistryView(APIView):
    serializer_class = GetPropertyRegistrySerializer
    @extend_schema(
        summary="등기부등본 조회",
        description="도로명 주소로 등기부등본을 조회합니다.",
        parameters=[GetPropertyRegistrySerializer],
        responses={200: (OpenApiTypes.BINARY, "application/pdf")},
        tags=["address_apis"],
    )
    def get(self, request):
        serializer = GetPropertyRegistrySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        full_addr = vd["roadAddr"] + " " + vd.get("details", "")
        pdf_bytes = get_property_registry(full_addr=full_addr)
        return FileResponse(
            BytesIO(pdf_bytes),
            as_attachment=True,
            filename="output.pdf",
            content_type="application/pdf",
        )

# 건물 정보 가져오기.
class GetBuildingInfoView(APIView):
    serializer_class = GetBuildingInfoSerializer
    @extend_schema(
        summary="건물 정보 확인.",
        description="건물 정보를 도로명 주소로 조회합니다.",
        parameters=[GetBuildingInfoSerializer],
        tags=["address_apis"],
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request):
        serializer = GetBuildingInfoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        # road address로 검색 진행, Parsing
        address:AddressManager = AddressManager(roadAddr=vd["roadAddr"])
        address.initialize(research=True)

        if not address.is_valid():
            return Response({"error": "유효하지 않은 주소입니다."}, status=400)
        
        info = BuildingInfoManager().makeInfo(address)
        
        return Response(info)

class UserPriceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserPrice.objects.all().order_by("-id")
    serializer_class = UserPriceSerializer
    
    
class BuildingInfoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BuildingInfo.objects.all().order_by("-id")
    serializer_class = BuildingInfoSerializer
    
    
class AvgPriceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AvgPrice.objects.all().order_by("-id")
    serializer_class = AvgPriceSerializer
    
    
class PropertyRegistryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PropertyRegistry.objects.all().order_by("-id")
    serializer_class = PropertyRegistrySerializer
    
    
class AirConditionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AirCondition.objects.all().order_by("-id")
    serializer_class = AirConditionSerializer    

class FloodViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Flood.objects.all().order_by("-id")
    serializer_class = FloodSerializer    
    
    
class PropertyBundleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PropertyBundle.objects.all().order_by("-id")
    serializer_class = PropertyBundleSerializer    
    