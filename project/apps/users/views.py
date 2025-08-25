from rest_framework import status, generics
from rest_framework.viewsets import ViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
    OpenApiParameter, OpenApiTypes, inline_serializer,
)

from .models import User, UserTendency
from .serializers import (RegisterSerializer, LoginSerializer, UserSerializer, UserTendencyWriteSerializer,
                          UserTendencyReadSerializer)
from django.shortcuts import get_object_or_404
from django.db import transaction

user_id_param = OpenApiParameter(
    name="user_id",
    location=OpenApiParameter.PATH,
    description="대상 사용자 ID",
    type=OpenApiTypes.INT,
    required=True,
)
    
class RegisterView(APIView):
    @extend_schema(
        summary="회원 가입",
        description="회원가입 진행.",
        request=RegisterSerializer,
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({ "message": "Register successed!"}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    @extend_schema(
        summary="로그인",
        description="로그인 진행 id를 반환.",
        request=LoginSerializer,
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            # 이 대상이 있는지 확인.
            try:
                user = User.objects.get(email=serializer.validated_data['email'])
            except User.DoesNotExist:
                return Response({"error": "Can't find user."}, status=status.HTTP_401_UNAUTHORIZED)
            
            return Response(
                {
                   "id": user.id,
                   "message": "Login successful."
                }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 디버그 용. list, retrieve만 있어 CRUD 기능 포함 안됨. 
class UserViewSet(ViewSet):
    @action(detail=False, methods=['get'], url_path='all')
    def list_users(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)
    

class UserTendencyView(APIView):
    @extend_schema(
        summary="사용자 성향 조회",
        description="user_id로 사용자 성향을 조회한다.",
        parameters=[user_id_param],
        responses={
            OpenApiTypes.OBJECT
        },
        tags=["UserTendency"]
    )
    def get(self, request, user_id: int):
        obj = get_object_or_404(UserTendency.objects.select_related("user"), user_id=user_id)
        read = UserTendencyReadSerializer(obj, context={"request": request})
        return Response(read.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="사용자 성향 추가.",
        description=(
            "body로 descrition을 전달합니다."
        ),
        parameters=[user_id_param],
        request=UserTendencyWriteSerializer,
        responses={
            OpenApiTypes.OBJECT
        },
        tags=["UserTendency"]
    )
    @transaction.atomic
    def post(self, request, user_id: int):
        # URL의 user가 실제 존재하는지 체크
        user = get_object_or_404(User, pk=user_id)

        # body 검증 (description만 받음)
        serializer = UserTendencyWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        description = serializer.validated_data["description"]

        # upsert
        obj, created = UserTendency.objects.update_or_create(
            user=user,
            defaults={"description": description},
        )

        read = UserTendencyReadSerializer(obj, context={"request": request})
        return Response(read.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    
class ListAllTendenciesView(generics.ListAPIView):
    serializer_class=UserTendencyReadSerializer
    queryset = UserTendency.objects.select_related("user").order_by("user_id")

    @extend_schema(
        summary="전체 사용자 성향 리스트",
        description="전체 UserTendency를 페이지네이션하여 반환합니다.",
        responses={
            OpenApiTypes.OBJECT
        },
        tags=["UserTendency"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
