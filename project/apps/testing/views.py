from django.shortcuts import render

# project/apps/testing/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import FloodDepthItemSerializer

from external.client.data_go_kr import DataGoKrClient

class FloodDepthProxyView(APIView):
    def get(self, request):
        client = DataGoKrClient()
        pass
