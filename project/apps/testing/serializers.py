# project/apps/testing/serializers.py
from rest_framework import serializers

# class FloodDepthItemSerializer(serializers.Serializer):
#     stdgCtpvCd = serializers.CharField(help_text="시도 코드 (예: 11=서울)")
#     stdgSggCd  = serializers.CharField(help_text="시군구 코드 (예: 680=강남구)")
#     fldlvFreq  = serializers.CharField(help_text="빈도 코드(030/050/080/100)", required=False)
#
#     floodAreaDepthLe05 = serializers.FloatField(required=False, help_text="≤0.5m 면적")
#     floodAreaDepth0510 = serializers.FloatField(required=False, help_text="0.5~1.0m 면적")
#     floodAreaDepth1020 = serializers.FloatField(required=False, help_text="1.0~2.0m 면적")
#     floodAreaDepth2050 = serializers.FloatField(required=False, help_text="2.0~5.0m 면적")
#     floodAreaDepthGt50 = serializers.FloatField(required=False, help_text="≥5.0m 면적")
#
#
# class FloodDepthResponseSerializer(serializers.Serializer):
#     header = serializers.DictField()
#     items  = FloodDepthItemSerializer(many=True)

# apps/testing/serializers.py
from rest_framework import serializers

# 1) 쿼리 파라미터(스웨거 폼 생성용)
class FloodDepthQuerySerializer(serializers.Serializer):
    stdgCtpvCd = serializers.CharField(required=True, help_text="시도코드(예: 11=서울)")
    stdgSggCd  = serializers.CharField(required=True, help_text="시군구코드(예: 680=강남구)")
    pageNo     = serializers.IntegerField(required=False, default=1, min_value=1)
    numOfRows  = serializers.IntegerField(required=False, default=10, min_value=1, max_value=1000)
    fldlvFreq  = serializers.CharField(required=False, help_text="빈도코드(030/050/080/100)")
    type       = serializers.ChoiceField(choices=["json", "xml"], required=False, default="json")
    cols       = serializers.CharField(required=False, help_text="응답 컬럼 지정(쉼표)")

# 2) 응답 아이템(침수심 통계 한 행)
class FloodDepthItemSerializer(serializers.Serializer):
    stdgCtpvCd = serializers.CharField()
    stdgSggCd  = serializers.CharField()
    fldlvFreq  = serializers.CharField(required=False, allow_blank=True)
    floodAreaDepthLe05  = serializers.FloatField(required=False, allow_null=True)
    floodAreaDepth0510  = serializers.FloatField(required=False, allow_null=True)
    floodAreaDepth1020  = serializers.FloatField(required=False, allow_null=True)
    floodAreaDepth2050  = serializers.FloatField(required=False, allow_null=True)
    floodAreaDepthGt50  = serializers.FloatField(required=False, allow_null=True)

# 3) 최상위 응답(헤더 + items[])
class FloodDepthResponseSerializer(serializers.Serializer):
    header = serializers.DictField()
    items  = FloodDepthItemSerializer(many=True)

# 4) 에러 메시지용(400/502 등)
class MessageSerializer(serializers.Serializer):
    detail = serializers.CharField()
