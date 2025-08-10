from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.shortcuts import render

from external.v_world import VWorldClient
from .serializers import VWorldSearchSerializer

# Create your views here.

class VWorldSearchView(APIView):
    @swagger_auto_schema(
        operation_summary="주소 검색",
        operation_description="장소를 검색합니다.",
        query_serializer=VWorldSearchSerializer
    )
    def get(self, request):
        serializer = VWorldSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        client = VWorldClient()
        data = client.search_address(
            query = serializer.validated_data["q"],
            size=serializer.validated_data["size"],
            page=serializer.validated_data["page"],
        )
        client.close()

        return Response(data)

