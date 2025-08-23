from rest_framework import serializers
from datetime import datetime
from typing import Optional
from .models import (BuildingInfo, PropertyRegistry, AirCondition, UserPrice,
                     AvgPrice)


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

### user_price serializer
class UserPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPrice
        fields = ["id", "is_year_rent", "security_deposit", "monthly_rent"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        return UserPrice.objects.create(**validated_data)

### user_price serializer
class BuildingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildingInfo
        fields = ["id", "description"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        return BuildingInfo.objects.create(**validated_data)
    
### user_price serializer
class AvgPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvgPrice
        fields = ["id", "avg_year_price", "avg_month_security_price", "avg_month_rent"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        return AvgPrice.objects.create(**validated_data)


class PropertyRegistrySerializer(serializers.ModelSerializer):
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = PropertyRegistry
        fields = ["id", "pdf", "pdf_url", "created"]
        read_only_fields = ["id", "created"]

    def get_pdf_url(self, obj):
        request = self.context.get("request")
        if obj.pdf and request:
            return request.build_absolute_uri(obj.pdf.url)
        return None

class AirConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirCondition
        fields = ["id", "data", "created"]
        read_only_fields = ["id", "created"]
        
        def create(self, validated_data):
            return AvgPrice.objects.create(**validated_data)

