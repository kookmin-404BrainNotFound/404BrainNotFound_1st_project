from django.shortcuts import render

# project/apps/testing/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status

from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
    OpenApiParameter, OpenApiTypes, inline_serializer
)

from .serializers import FloodDepthItemSerializer, RoadAddressSerializer

from external.client.data_go_kr import DataGoKrClient
from external.address.address_manager import AddressManager

class FloodDepthProxyView(APIView):
    @extend_schema(
        summary="침수 확인",
        description="침수 정도를 확인합니다.",
        parameters=[RoadAddressSerializer],
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request:Request):
        serializer = RoadAddressSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        
        address_manager:AddressManager = AddressManager(vd["road_address"])
        address_manager.initialize()
        
        client = DataGoKrClient()
        data = client.getFloodByAddress(address=address_manager)
        
        client.close()
        
        return Response(data)
