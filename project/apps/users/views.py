from rest_framework import status, generics
from rest_framework.viewsets import ViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User, UserTendency
from .serializers import (RegisterSerializer, LoginSerializer, UserSerializer, UserTendencyWriteSerializer,
                          UserTendencyReadSerializer)
from django.shortcuts import get_object_or_404
from django.db import transaction

user_id_param = openapi.Parameter(
    name="user_id",
    in_=openapi.IN_PATH,
    description="대상 사용자 ID",
    type=openapi.TYPE_INTEGER,
    required=True,
)
    
class RegisterView(APIView):
    @swagger_auto_schema(
        operation_summary="회원 가입",
        operation_description="회원가입 진행.",
        request_body=RegisterSerializer,
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({ "message": "Register successed!"}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    @swagger_auto_schema(
        operation_summary="로그인",
        operation_description="로그인 진행 id를 반환.",
        request_body=LoginSerializer,
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
                    # 추후에 JWT 토큰 추가 필요.
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
    @swagger_auto_schema(
        operation_summary="사용자 성향 조회",
        operation_description="user_id로 사용자 성향을 조회한다.",
        manual_parameters=[user_id_param],
        responses={
            200: openapi.Response("조회 성공", UserTendencyReadSerializer),
            404: openapi.Response("user 또는 사용자 성향 없음."),
        },
        tags=["UserTendency"]
    )
    def get(self, request, user_id: int):
        obj = get_object_or_404(UserTendency.objects.select_related("user"), user_id=user_id)
        read = UserTendencyReadSerializer(obj, context={"request": request})
        return Response(read.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="사용자 성향 추가.",
        operation_description=(
            "body로 descrition을 전달합니다."
        ),
        manual_parameters=[user_id_param],
        request_body=UserTendencyWriteSerializer,
        responses={
            201: openapi.Response("생성됨", UserTendencyReadSerializer),
            200: openapi.Response("업데이트됨", UserTendencyReadSerializer),
            400: "유효하지 않은 요청 바디",
            404: "user_id가 존재하지 않음",
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

    @swagger_auto_schema(
        operation_summary="전체 사용자 성향 리스트",
        operation_description="전체 UserTendency를 페이지네이션하여 반환합니다.",
        responses={
            200: openapi.Response(
                "리스트 성공",
                UserTendencyReadSerializer(many=True)
            ),
        },
        tags=["UserTendency"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
