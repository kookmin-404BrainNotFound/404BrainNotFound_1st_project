from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
    OpenApiParameter, OpenApiTypes, inline_serializer,
)

from .models import Contract
from .serializers import ContractSerializer, UploadImagesSerializer, UploadResultSerializer, UploadResultItemSerializer

from external.gpt.gpt_manager import *

from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

class ContractViewSet(ModelViewSet):
    queryset = Contract.objects.all().order_by('-created')
    serializer_class = ContractSerializer
    parser_classes = [MultiPartParser, FormParser]     # 파일 업로드 필수
    permission_classes = [AllowAny]   # GET은 누구나, POST/DELETE는 인증 필요


# gpt에 업로드. 주소를 파악하라고 함. 여러개를 업로드 가능.
class StartContractView(APIView):
    @extend_schema(
        tags=["Contract"],
        summary="이미지 업로드 (GPT file_id 발급)",
        description="여러 이미지를 받아 OpenAI Files API에 업로드하고 file_id 목록을 반환합니다.",
        request={"multipart/form-data": UploadImagesSerializer},
        responses={201: UploadResultSerializer, 400: OpenApiTypes.OBJECT, 502: OpenApiTypes.OBJECT},
    )
    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist("images")
        if not files:
            return Response({"details": "이미지가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
    
        results = []
        
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

            results.append({
                "filename": f.name,
                "file_id": file_id,
                "content_type": ctype,
                "size": getattr(f, "size", None),
            })

        return Response({"files": results}, status=status.HTTP_201_CREATED)

