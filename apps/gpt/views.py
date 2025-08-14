from django.shortcuts import render

from .serializers import GptTestSerializer
from external.gpt.gpt_manager import *
from drf_yasg.utils import swagger_auto_schema

from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.

class GptTestView(APIView):
    @swagger_auto_schema(
        operation_summary="GPT 테스트",
        operation_description="GPT에 질문을 보내고 응답을 받습니다.",
        query_serializer=GptTestSerializer
    )
    def get(self, request):
        serializer = GptTestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]
        print(question)
        response = asyncio.run(test_gpt(question))
        return Response({"response": response})
    
