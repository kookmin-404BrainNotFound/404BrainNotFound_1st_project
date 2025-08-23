from rest_framework import serializers
from datetime import datetime
from typing import Optional
from .models import BuildingInfo, PropertyRegistry, AirCondition


class AddressSearchSerializer(serializers.Serializer):
    q = serializers.CharField(max_length=200)
    size = serializers.IntegerField(required=False, max_value=1000, default=10)
    page = serializers.IntegerField(required = False, min_value=1, default=1)

class GetPriceSerializer(serializers.Serializer):
    size = serializers.IntegerField(required=False, max_value=1000, default=10)
    year = serializers.IntegerField(required=False, max_value=2100, default=datetime.now().year)
    
    roadAddr = serializers.CharField(max_length=200, required=True)


class GetPropertyRegistrySerializer(serializers.Serializer):
    roadAddr = serializers.CharField(max_length=200, required=True)
    details = serializers.CharField(max_length=200, required=False, allow_blank=True)


class GetBuildingInfoSerializer(serializers.Serializer):
    roadAddr = serializers.CharField(max_length=200, required=True)

class PropertyRegistrySerializer(serializers.ModelSerializer):
    report_id = serializers.IntegerField(source="report.id", read_only=True)
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = PropertyRegistry
        fields = ["id", "report", "report_id", "pdf", "pdf_url", "created"]
        read_only_fields = ["id", "created"]

    def get_pdf_url(self, obj):
        request = self.context.get("request")
        if obj.pdf and request:
            return request.build_absolute_uri(obj.pdf.url)
        return None

class AirConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirCondition
        fields = ["id", "report", "data", "created"]
        read_only_fields = ["id", "created"]
        