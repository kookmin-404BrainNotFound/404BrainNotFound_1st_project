from rest_framework import serializers
from external.address.address import Address
from datetime import datetime

class AddressSearchSerializer(serializers.Serializer):
    q = serializers.CharField(max_length=200)
    size = serializers.IntegerField(required=False, max_value=1000, default=10)
    page = serializers.IntegerField(required = False, min_value=1, default=1)

class GetPriceSerializer(serializers.Serializer):
    size = serializers.IntegerField(required=False, max_value=1000, default=10)
    year = serializers.IntegerField(required=False, max_value=2100, default=datetime.now().year)
    
    roadAddr = serializers.CharField(max_length=200, required=True)

    