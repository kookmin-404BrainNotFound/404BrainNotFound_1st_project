from rest_framework import serializers
from .models import User, UserTendency

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'name']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name']
            )
        user.save()
        return user
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


# 디버그 용 전체 Serializer.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'created_at']

# 주거 성향.
class UserTendencyReadSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = UserTendency
        fields = ["user", "description"]

    def get_user(self, obj):
        return {"id": obj.user_id, "username": obj.user.name}

class UserTendencyWriteSerializer(serializers.Serializer):
    description = serializers.JSONField()


