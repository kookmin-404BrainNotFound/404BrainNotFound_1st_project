from rest_framework import serializers
from .models import Contract

class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ['id', 'image', 'caption', 'created']

    def validate_image(self, image):
        # 용량 제한 예: 5MB
        if image.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('이미지 용량은 5MB 이하만 가능합니다.')
        # MIME 타입 간단 체크
        ct = getattr(image, 'content_type', '')
        if not ct.startswith('image/'):
            raise serializers.ValidationError('이미지 파일만 업로드 가능합니다.')
        return image

class UploadImagesSerializer(serializers.Serializer):
    images = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=False,
        help_text="여러 이미지를 같은 키(images)로 첨부하세요"
    )

class UploadResultItemSerializer(serializers.Serializer):
    filename = serializers.CharField()
    file_id = serializers.CharField()
    content_type = serializers.CharField(required=False, allow_null=True)
    size = serializers.IntegerField(required=False, allow_null=True)

class UploadResultSerializer(serializers.Serializer):
    files = UploadResultItemSerializer(many=True)
