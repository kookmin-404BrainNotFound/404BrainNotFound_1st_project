# project/apps/testing/serializers.py
from rest_framework import serializers

class RoadAddressSerializer(serializers.Serializer):
    road_address = serializers.CharField()
    