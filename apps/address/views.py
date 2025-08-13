from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.shortcuts import render

from external.business_juso import BusinessJusoClient
from external.seoul_data import DataSeoulClient
from .serializers import AddressSearchSerializer

# Create your views here.

class AddressSearchView(APIView):
    @swagger_auto_schema(
        operation_summary="주소 검색",
        operation_description="장소를 검색합니다.",
        query_serializer=AddressSearchSerializer
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

# 전월세가 가져오기
class GetPriceView(APIView):
    def get(self, request):
        client = DataSeoulClient()
        data = client.getPrice()
        return Response(data)

