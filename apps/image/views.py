from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny

from .models import image
from .serializers import ImageSerializer

class ImageViewSet(ModelViewSet):
    queryset = image.objects.all().order_by('-created')
    serializer_class = ImageSerializer
    parser_classes = [MultiPartParser, FormParser]     # 파일 업로드 필수
    permission_classes = [AllowAny]   # GET은 누구나, POST/DELETE는 인증 필요

