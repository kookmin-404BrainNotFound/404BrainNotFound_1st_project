import inspect

from rest_framework import viewsets, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.shortcuts import render
from io import BytesIO
from django.http import FileResponse

from external.client.business_juso import BusinessJusoClient
from external.client.seoul_data import DataSeoulClient
from external.client.a_pick import APickClient
from external.address.building_info import BuildingInfoManager
from external.address.property_registry import get_property_registry

from external.address.address_manager import AddressManager
from .serializers import (AddressSearchSerializer, GetPriceSerializer,
                          GetPropertyRegistrySerializer, GetBuildingInfoSerializer, PropertyRegistrySerializer,
                          UserPriceSerializer, BuildingInfoSerializer, AvgPriceSerializer,
                          AirConditionSerializer, PropertyBundleSerializer)
from .models import (UserPrice, BuildingInfo, AvgPrice, PropertyRegistry,
                     AirCondition, PropertyBundle)

# Create your views here.

class AddressSearchView(APIView):
    @swagger_auto_schema(
        operation_summary="주소 검색",
        operation_description="장소를 검색합니다.",
        query_serializer=AddressSearchSerializer,
        tags=["address_apis"],
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
    @swagger_auto_schema(
        operation_summary="전월세 가격 조회.",
        operation_description="전월세 가격을 도로명 주소로 조회합니다.",
        query_serializer=GetPriceSerializer,
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
    @swagger_auto_schema(
        operation_summary="등기부등본 조회",
        operation_description="도로명 주소로 등기부등본을 조회합니다.",
        query_serializer=GetPropertyRegistrySerializer,
        produces=["application/pdf"],
        responses={200: openapi.Response(
            description="PDF file",
            schema=openapi.Schema(type=openapi.TYPE_STRING, format="binary")
        )},
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
            as_attachment=True,                # 다운로드 강제 (뷰어로 열고 싶으면 False)
            filename="output.pdf",             # 원하면 동적으로 바꾸세요
            content_type="application/pdf",
        )

# 건물 정보 가져오기.
class GetBuildingInfoView(APIView):
    @swagger_auto_schema(
        operation_summary="건물 정보 확인.",
        operation_description="건물 정보를 도로명 주소로 조회합니다.",
        query_serializer=GetBuildingInfoSerializer,
        tags=["address_apis"],
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
    
    
class PropertyBundleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PropertyBundle.objects.all().order_by("-id")
    serializer_class = PropertyBundleSerializer    
    