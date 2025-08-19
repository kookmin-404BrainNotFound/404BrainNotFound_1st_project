from rest_framework import serializers
from .models import image

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = image
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
