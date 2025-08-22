from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

class StartReportSerializer(serializers.Serializer):
    road_address = serializers.CharField(max_length=255)
    details = serializers.CharField(max_length=500, required=False, allow_blank=True)

class SaveUserPriceSerializer(serializers.Serializer):
    security_deposit = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    monthly_rent = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    is_year_rent = serializers.BooleanField(default=False)
    
class MakeAvgPriceReportSerializer(serializers.Serializer):
    start_year = serializers.IntegerField(required=False, allow_null=True, default=2024)

class MakeReportSerializer(serializers.Serializer):
    is_property_registry = serializers.BooleanField(required=False, allow_null=True, default=False)

