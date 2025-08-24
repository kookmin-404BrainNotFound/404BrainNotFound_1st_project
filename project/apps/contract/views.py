from rest_framework import viewsets, generics
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
    OpenApiParameter, OpenApiTypes, inline_serializer,
)

from .models import Contract, ContractData
from .serializers import (ContractSerializer, UploadImagesSerializer,
                           UploadResultSerializer, UploadResultItemSerializer, ContractDataSerializer,
                           ContractAddressListSerializer)

from apps.users.models import User

from external.gpt.gpt_manager import *

from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

import json
class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all().order_by('-created')
    serializer_class = ContractSerializer

    http_method_names = ["get", "delete"]


# gpt에 업로드. 주소를 파악하라고 함. 여러개를 업로드 가능.
class StartContractView(APIView):
    @extend_schema(
        tags=["Contract"],
        summary="이미지 업로드 (GPT file_id 발급)",
        description="여러 이미지를 받아 OpenAI Files API에 업로드하고 file_id 목록을 반환합니다.",
        request={"multipart/form-data": UploadImagesSerializer},
        responses={201: UploadResultSerializer, 400: OpenApiTypes.OBJECT, 502: OpenApiTypes.OBJECT},
    )
    def post(self, request, user_id):
        files = request.FILES.getlist("images")
        if not files:
            return Response({"details": "이미지가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        images = []
        
        for f in files:
            ctype = getattr(f, "content_type", "") or ""
            if not ctype.startswith("image/") and not ctype.endswith("/pdf"):
                return Response(
                    {"details": f"허용하지 않는 파일 형식입니다: {ctype}", "filename": f.name},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if isinstance(f, InMemoryUploadedFile):
                data = f.read()
            elif isinstance(f, TemporaryUploadedFile):
                # 큰 파일 대비
                buf = BytesIO()
                for chunk in f.chunks():
                    buf.write(chunk)
                data = buf.getvalue()
            else:
                # fallback
                data = f.read()

            # GPT Files API 업로드 → file_id 획득
            try:
                file_id = get_gpt_file_id(
                    file_bytes=data,
                    filename=f.name,
                    purpose="user_data"  # 또는 "assistants" 등 프로젝트 정책에 맞게
                )
            except Exception as e:
                return Response(
                    {"details": f"파일 업로드 실패: {f.name}", "error": str(e)},
                    status=status.HTTP_502_BAD_GATEWAY
                )

            images.append({
                "filename": f.name,
                "file_id": file_id,
                "content_type": ctype,
                "size": getattr(f, "size", None),
            })

        text_path = settings.TEXT_ROOT
        with open(text_path / "prompt/get_address.txt", "r", encoding="utf-8") as f:
            get_address_prompt = f.read()
        # gpt에게 주소와 상세주소 물어보기.
        messages = []

        for img in images:
            message = create_message("user", [
                {"type": "input_image", "file_id": img["file_id"]}
            ])
            messages.append(message)
        messages.append(create_message("user", get_address_prompt))
        answer = ask_gpt(messages, 'gpt-4.1')
        print(answer)

        # json으로 변환.
        address_json = json.loads(answer)

        result = {
            "images": images,         # list OK
            "answer": address_json,   # dict(JSON)이나 fallback
        }

        # contract에 save하기.
        serializer = ContractSerializer(data={"description": result})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

# 다시 contract id로써 계약서 분석을 요청한다.
class AnalyzeContractView(APIView):
    @extend_schema(
        tags=["Contract"],
        summary="계약서 분석 요청.",
        description="여러 이미지를 받아 계약서를 분석합니다.",
    )
    def post(self, request, contract_id):
        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)
        
        text_path = settings.TEXT_ROOT
        with open(text_path / "prompt/analyze_contract.txt", "r", encoding="utf-8") as f:
            analyze_contract_prompt = f.read()

        messages = []

        images = contract.description["images"]

        for img in images:
            message = create_message("user", [
                {"type": "input_image", "file_id": img["file_id"]}
            ])
            messages.append(message)
        messages.append(create_message("user", analyze_contract_prompt))
        answer = ask_gpt(messages, 'gpt-4.1')
        answer_json = json.loads(answer)

        serializer = ContractDataSerializer(data={"description": answer_json})
        serializer.is_valid(raise_exception=True)
        serializer.save(contract=contract)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class ContractDataViewSet(viewsets.ModelViewSet):
    queryset = ContractData.objects.all().order_by("-id")
    serializer_class = ContractDataSerializer

    http_method_names = ["get", "delete"]


# 사용자로 계약서 요약을 조회한다.
class ContractByUserListView(generics.ListAPIView):
    serializer_class = ContractAddressListSerializer

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        return (
            Contract.objects
            .filter(user_id=user_id)
            .order_by("-created")
        )
        