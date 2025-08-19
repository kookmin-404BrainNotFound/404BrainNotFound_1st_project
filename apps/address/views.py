from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.shortcuts import render

from external.client.business_juso import BusinessJusoClient
from external.client.seoul_data import DataSeoulClient

from external.address.address import Address
from .serializers import AddressSearchSerializer, GetPriceSerializer

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

# 전월세가 가져오기 검색 API에서 파싱해서 다시 전달필요함.
class GetPriceView(APIView):
    @swagger_auto_schema(
        operation_summary="전월세 가격 조회.",
        operation_description="전월세 가격을 도로명 주소로 조회합니다.",
        query_serializer=GetPriceSerializer,
    )
    def get(self, request):
        serializer = GetPriceSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        


        address = None
        if vd["admCd"]:
            address = Address(
                roadAddr=vd["roadAddr"],
                bdNm=vd["bdNm"],
                admCd=vd["admCd"],
                sggNm=vd["sggNm"],
                mtYn=vd["mtYn"],
                lnbrMnnm=vd["lnbrMnnm"],
                lnbrSlno=vd["lnbrSlno"],
            )
            print(f"Address created: {address}")
            if not address.is_valid():
                return Response({"detail": "Invalid address payload"}, status=400)

        client = DataSeoulClient()
        
        data = client.getPrice(
            size = vd["size"],
            year = vd["year"],
            address = address,
        )
        client.close()
        
        return Response(data)

