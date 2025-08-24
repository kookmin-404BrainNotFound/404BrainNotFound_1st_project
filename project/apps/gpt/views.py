from django.shortcuts import render

from .serializers import GptTestSerializer
from external.gpt.gpt_manager import *
from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
    OpenApiParameter, OpenApiTypes, inline_serializer,
)

from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.

class GptTestView(APIView):
    @extend_schema(
        summary="GPT 테스트",
        description="GPT에 질문을 보내고 응답을 받습니다.",
        parameters=[GptTestSerializer],
    )
    def get(self, request):
        serializer = GptTestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]
        response = test_gpt(question)
        return Response({"response": response})
    
