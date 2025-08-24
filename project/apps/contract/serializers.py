from rest_framework import serializers
from .models import Contract, ContractData

class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ['id', 'user', 'description','created']
        extra_kwargs = {
            "user": {"write_only": True, "required": False}
        }

class ContractDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractData
        fields = ['id', 'contract', 'description']
        read_only_fields = ["id"]
        extra_kwargs = {
            "contract": {"write_only": True, "required":False},
        }

    def create(self, validated_data):
        return ContractData.objects.create(**validated_data)

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

class ContractAddressListSerializer(serializers.ModelSerializer):
    contract_id = serializers.IntegerField(source="id", read_only=True)

    # created 를 created_at 이름으로 노출
    created_at = serializers.DateTimeField(source="created", read_only=True)
    # description JSON 안에서 address만 꺼내기
    address = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = ("contract_id", "created_at", "address")

    def get_address(self, obj):
        desc = obj.description or {}
        if isinstance(desc, dict) and "answer" in desc:
            return desc.get("answer").get("address")
        return (
            desc.get("주소")
            or (desc.get("임대 목적물") or {}).get("주소")
            or None
        )
