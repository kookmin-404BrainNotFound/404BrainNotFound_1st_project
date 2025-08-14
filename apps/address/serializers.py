from rest_framework import serializers
from external.address.address import Address

class AddressSearchSerializer(serializers.Serializer):
    q = serializers.CharField(max_length=200)
    size = serializers.IntegerField(required=False, max_value=1000, default=10)
    page = serializers.IntegerField(required = False, min_value=1, default=1)

class GetPriceSerializer(serializers.Serializer):
    size = serializers.IntegerField(required=False, max_value=1000, default=10)
    year = serializers.IntegerField(required=False, max_value=2100, default=None)
    
    roadAddr = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    bdNm = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    admCd = serializers.CharField(max_length=10, required=False, allow_blank=True, default="")
    sggNm = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    mtYn = serializers.CharField(max_length=1, required=False, allow_blank=True, default="")
    lnbrMnnm = serializers.CharField(max_length=10, required=False, allow_blank=True, default="")
    lnbrSlno = serializers.CharField(max_length=10, required=False, allow_blank=True, default="")
    