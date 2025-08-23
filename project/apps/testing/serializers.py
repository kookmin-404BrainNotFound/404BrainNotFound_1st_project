# project/apps/testing/serializers.py
from rest_framework import serializers

class FloodDepthItemSerializer(serializers.Serializer):
    stdgCtpvCd = serializers.CharField(help_text="시도 코드 (예: 11=서울)")
    stdgSggCd  = serializers.CharField(help_text="시군구 코드 (예: 680=강남구)")
    fldlvFreq  = serializers.CharField(help_text="빈도 코드(030/050/080/100)", required=False)

    floodAreaDepthLe05 = serializers.FloatField(required=False, help_text="≤0.5m 면적")
    floodAreaDepth0510 = serializers.FloatField(required=False, help_text="0.5~1.0m 면적")
    floodAreaDepth1020 = serializers.FloatField(required=False, help_text="1.0~2.0m 면적")
    floodAreaDepth2050 = serializers.FloatField(required=False, help_text="2.0~5.0m 면적")
    floodAreaDepthGt50 = serializers.FloatField(required=False, help_text="≥5.0m 면적")


class FloodDepthResponseSerializer(serializers.Serializer):
    header = serializers.DictField()
    items  = FloodDepthItemSerializer(many=True)
