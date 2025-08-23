from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny

from .models import Contract
from .serializers import ContractSerializer

class ContractViewSet(ModelViewSet):
    queryset = Contract.objects.all().order_by('-created')
    serializer_class = ContractSerializer
    parser_classes = [MultiPartParser, FormParser]     # 파일 업로드 필수
    permission_classes = [AllowAny]   # GET은 누구나, POST/DELETE는 인증 필요

