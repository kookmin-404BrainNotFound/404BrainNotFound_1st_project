from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

class ReportRunSerializer(serializers.Serializer):
    road_address = serializers.CharField(max_length=255)
    details = serializers.CharField(max_length=500, required=False, allow_blank=True)

class SavePriceSerializer(serializers.Serializer):
    report_run_id = serializers.IntegerField()
    security_deposit = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    monthly_rent = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)