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
        extra_kwargs = {
            "report": {"write_only": True, "required":False},
        }

    def create(self, validated_data):
        return ReportData.objects.create(**validated_data)

class ReportSummarySerializer(serializers.ModelSerializer):
    # Subquery로 annotate된 값들을 그대로 직렬화
    danger_score = serializers.IntegerField(read_only=True, allow_null=True)
    fit_score = serializers.IntegerField(read_only=True, allow_null=True)
    security_deposit = serializers.IntegerField(read_only=True, allow_null=True)
    monthly_rent = serializers.IntegerField(read_only=True, allow_null=True)
    is_year_rent = serializers.BooleanField(read_only=True, allow_null=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "created_at",
            "status",
            "danger_score",
            "fit_score",
            "is_year_rent",
            "security_deposit",
            "monthly_rent",
        ]
