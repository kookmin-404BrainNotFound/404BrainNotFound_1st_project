from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from .models import ReportData, Report

from apps.users.models import User

class StartReportSerializer(serializers.Serializer):
    road_address = serializers.CharField(max_length=255)
    details = serializers.CharField(max_length=500, required=False, allow_blank=True)
    user_id = serializers.IntegerField(required=True)
    
class SaveUserPriceDocSerializer(serializers.Serializer):
    security_deposit = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    monthly_rent = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    is_year_rent = serializers.BooleanField(default=False)
    
class MakeAvgPriceDocSerializer(serializers.Serializer):
    start_year = serializers.IntegerField(required=False, allow_null=True, default=2024)

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["id", "created_at", "status", "user"]
        read_only_fields = ["id", "created_at", "user"]

# reportData serializer
class ReportDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportData
        fields = ["id", "report", "score", "description", "type", "created"]
        read_only_fields = ["id", "created"]
        