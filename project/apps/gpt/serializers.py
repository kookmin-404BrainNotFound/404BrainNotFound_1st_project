from rest_framework import serializers


class GptTestSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500)



