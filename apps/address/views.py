from rest_framework.views import APIView
from rest_framework.response import Response

from django.shortcuts import render

from external.v_world import VWorldClient
from .serializers import VWorldSearchSerializer

# Create your views here.

class VWorldSearchView(APIView):
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

