from django.core.files.base import ContentFile
from django.http import Http404
from django.db import transaction
from django.utils.decorators import method_decorator
from django.db.models import OuterRef, Subquery

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, viewsets

from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
    OpenApiParameter, OpenApiTypes, inline_serializer,
)

from apps.users.models import User, UserTendency
from apps.users.serializers import UserTendencyReadSerializer

from .models import Report, ReportData
from .serializers import (StartReportSerializer, SaveUserPriceDocSerializer, MakeAvgPriceDocSerializer,
                           ReportDataSerializer, ReportSerializer, ReportSummarySerializer)

from external.address.building_info import BuildingInfoManager
from external.address.price import get_avg_price
from external.address.address_manager import AddressManager
from external.address.property_registry import get_property_registry
from apps.address.serializers import (PropertyRegistrySerializer, AirConditionSerializer,
                                      UserPriceSerializer, BuildingInfoSerializer, AvgPriceSerializer)
from apps.address.models import (Address, UserPrice, BuildingInfo, AvgPrice, PropertyRegistry,
                                 AirCondition, PropertyBundle)

from external.client.seoul_data import DataSeoulClient
from external.gpt.gpt_manager import *

import json, os

# Create your views here.

report_id_param = OpenApiParameter(
    name="report_id",
    type=OpenApiTypes.INT,                 # ✅ 타입
    location=OpenApiParameter.PATH,        # ✅ 경로 변수
    description="대상 Report ID",
    required=True,
)

# 보고서 작성을 시작한다.
class StartReportView(APIView):
    @extend_schema(
        summary="보고서 시작",
        description="새로운 보고서를 시작합니다.",
        parameters=[StartReportSerializer],
    )
    def post(self, request):
        serializer = StartReportSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        
        user_id = vd["user_id"]
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # 새 property bundle 생성.
        property_bundle = PropertyBundle.objects.create(user=user)

        # 새 report 객체 생성.
        report = Report.objects.create(property_bundle=property_bundle)

        # 주소 검색 및 Address 객체 만들기.
        address_manager = AddressManager(roadAddr=vd["road_address"])
        address_manager.initialize(research=True)
        if not address_manager.is_valid():
            return Response({"error": "유효하지 않은 주소입니다."}, status=status.HTTP_400_BAD_REQUEST)
        address_manager.details = vd.get("details", "")

        # 모델 필드명에 맞춰 저장 (road_addr)
        address = Address.objects.create(
            road_address=address_manager.roadAddr,
            bd_nm=address_manager.bdNm,
            adm_cd=address_manager.admCd,
            sgg_nm=address_manager.sggNm,
            mt_yn=address_manager.mtYn,
            lnbr_mnnm=address_manager.lnbrMnnm,
            lnbr_slno=address_manager.lnbrSlno,
            details=address_manager.details,
        )
        # address를 property_bundle과 연결.
        property_bundle.address = address
        property_bundle.save(update_fields=["address"])

        # 응답은 원시 타입/딕셔너리만
        return Response(
            {
                "report_id": report.id,
                "property_bundle_id": property_bundle.id,
                "address_id": address.id,
                "address": address_manager.as_dict(),
            },
            status=status.HTTP_201_CREATED,
        )
    
# 전월세가저장.
class SaveUserPriceView(APIView):
    @extend_schema(
        summary="전월세가 저장",
        description="전월세가 정보를 저장합니다.",
        parameters=[
            SaveUserPriceDocSerializer,
            report_id_param,
            ],
        tags=["report_danger"],
    )
    def post(self, request, report_id):
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)

        # property bundle 가져오기.
        property_bundle = report.property_bundle

        serializer = UserPriceSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # 가격 저장
        user_price = serializer.save()
        property_bundle.user_price = user_price
        property_bundle.save(update_fields=["user_price"])

        return Response(serializer.data, status=status.HTTP_201_CREATED)

# 건축물대장부 가져오기.
class MakeBuildingInfoView(APIView):
    @extend_schema(
        summary="건축물대장부 저장",
        description="건축물대장부를 저장합니다.",
        parameters=[report_id_param],
        tags=["report_danger"],
    )
    def post(self, request, report_id):
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # property_bundle 가져오기.
        property_bundle = report.property_bundle

        # 주소 가져오기.
        address_manager:AddressManager = property_bundle.address.to_address_manager()
        address_manager.initialize(research=False)
        
        # 건축물대장부
        info = BuildingInfoManager().makeInfo(address_manager)
        serializer = BuildingInfoSerializer(data={"description": info})
        serializer.is_valid(raise_exception=True)
        building_info = serializer.save()
        property_bundle.building_info = building_info
        property_bundle.save(update_fields=["building_info"])
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# 전월세가 평균 계산하기.
class MakeAvgPriceView(APIView):
    @extend_schema(
        summary="전월세가 평균계산",
        description="전월세가 평균을 계산해 저장합니다.",
        parameters=[
            MakeAvgPriceDocSerializer,
            report_id_param,
        ],
        tags=["report_danger"],
    )
    def post(self, request, report_id):
        docSerializer = MakeAvgPriceDocSerializer(data=request.query_params)
        docSerializer.is_valid(raise_exception=True)
        vd = docSerializer.validated_data
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # property_bundle 가져오기.
        property_bundle = report.property_bundle

        # 주소 가져오기.
        address_manager:AddressManager = property_bundle.address.to_address_manager()
        address_manager.initialize(research=False)
        
        # 전월세가분석
        price_info = get_avg_price(
            startYear=vd.get("start_year", 2024),
            address_manager=address_manager
        )
        
        serializer = AvgPriceSerializer(data=price_info)
        serializer.is_valid(raise_exception=True)
        avg_price = serializer.save()

        property_bundle.avg_price = avg_price
        property_bundle.save(update_fields=["avg_price"])
    
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# 등기부등본 조회뷰.
class MakePropertyRegistryView(APIView):
    @extend_schema(
        summary="등기부등본 저장",
        description="등기부등본을 저장합니다.",
        parameters=[
            MakeAvgPriceDocSerializer,
            report_id_param,
        ],
        tags=["report_danger"],
    )
    def post(self, request, report_id):
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # property_bundle 가져오기.
        property_bundle = report.property_bundle

        # 주소 가져오기.
        address_manager:AddressManager = property_bundle.address.to_address_manager()
        address_manager.initialize(research=False)
        
        # 등기부등본 조회하기.
        full_addr = address_manager.getFullAddr()
        pdf_bytes = get_property_registry(full_addr=full_addr)
        filename = "등기부등본.pdf"
        
        property_registry = PropertyRegistry()
        property_registry.pdf.save(filename, ContentFile(pdf_bytes), save=True)
        
        property_bundle.property_registry = property_registry
        property_bundle.save(update_fields=["property_registry"])

        serializer = PropertyRegistrySerializer(property_registry)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        
####### 적합도 시작 ########
class MakeAirConditionView(APIView):
    @extend_schema(
        summary="공기질 데이터 저장.",
        description="공기질 데이터를 저장합니다.",
        parameters=[report_id_param],
        tags=["report_fit"],
    )
    def post(self, request, report_id):
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # property_bundle 가져오기.
        property_bundle = report.property_bundle

        # 주소 가져오기.
        address_manager:AddressManager = property_bundle.address.to_address_manager()
        address_manager.initialize(research=False)

        client = DataSeoulClient()
        response = client.get_yearly_by_gu(2024, address_manager.sggNm)

        # db에 임시 저장하기.
        serializer = AirConditionSerializer(data=response)
        serializer.is_valid()
        air_condition = serializer.save()

        property_bundle.air_condition = air_condition
        property_bundle.save(update_fields=["air_condition"])
        return Response(serializer.data)

        
# 마지막 레포트 뷰. gpt에게 맡기는 역할만 수행.
class MakeReportFinalView(APIView):
    @extend_schema(
        summary="보고서 생성",
        description="보고서를 생성합니다.",
        parameters=[report_id_param],
    )
    def post(self, request, report_id):
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({'error': 'ReportRun not found'}, status=status.HTTP_404_NOT_FOUND)


        property_bundle = report.property_bundle
        ##### 위험도측정 #####
        # 주소 만들기
        address_manager:AddressManager = property_bundle.address.to_address_manager()
        address_manager.initialize(research=False)
                
        # 건축물대장부 그냥 string으로 가져온다.
        building_info = property_bundle.building_info.description
        # 전월세가분석
        avg_price:AvgPrice = property_bundle.avg_price
        price_info = AvgPriceSerializer(avg_price).data
        
        # user의 전월세가
        user_price:UserPrice = property_bundle.user_price
        user_price_info = UserPriceSerializer(user_price).data

        # 파일을 제외한 dict
        infos = {
            "building_info": building_info,
            "user_price_info": user_price_info,
            "price_info": price_info,
        }
        # 등기부등본 있으면 가져오기.
        pdf_bytes = None
        try:
            pr = property_bundle.property_registry
            with pr.pdf.open("rb") as f:
                pdf_bytes = f.read()
        except Exception as e:
            pdf_bytes = None
            
        ##################
        
        ##### 적합도 측정 #####

        # user를 가져오기.
        user:User = property_bundle.user
        # usertendency를 가져오기.
        user_tendency = UserTendencyReadSerializer(user.user_tendency).data
        print(user_tendency)

        # 공기질 가져오기.
        air_condiion = AirConditionSerializer(property_bundle.air_condition).data
        print(air_condiion)   
        
        # gpt에 물어본다. 처음에는 파일을 제외하고, 파일까지 첨부한 후 물어본다.
        messages = []

        ### textfolder_path
        text_path = settings.TEXT_ROOT
        
        # system
        with open(text_path / "sys/report_sys.txt", "r", encoding="utf-8") as f:
            system_str = f.read()
        # danger_prompt
        with open(text_path / "prompt/danger_report.txt", "r", encoding="utf-8") as f:
            danger_prompt = f.read()
        # fit prompt
        with open(text_path / "prompt/fit_report.txt", "r", encoding="utf-8") as f:
            fit_prompt = f.read()
        
        messages.append(create_message("system", system_str))
        
        #### 여기부터 위험도 분석 ####
        # 건축물 대장부 등 받기.
        messages.append(create_message("user", str(infos)))
        # gpt에게 등기부등본 보내기.
        if pdf_bytes is not None:
            pdf_file_id = get_gpt_file_id(pdf_bytes, "registry.pdf", "user_data")
            message = create_message("user", [
                {"type": "input_file", "file_id": pdf_file_id},
                {"type": "input_text", "text": "등기부등본 파일이야."}
            ])
            messages.append(message)
        # 먼저 위험도 분석하기.
        messages.append(create_message("user", danger_prompt))
        danger_response = ask_gpt(messages, model="gpt-4.1")
        
        # 사용자 성향 데이터 받기.
        messages.append(create_message("user", str(user_tendency)))
        # 공기질 데이터 넣기.
        messages.append(create_message("user", str(air_condiion)))
        # 침수 데이터 넣기.
        messages.append(create_message("user", ""))
        # 적합도 데이터 분석
        messages.append(create_message("user", fit_prompt))
        fit_response = ask_gpt(messages, model='gpt-4.1')
        
        # 파일 삭제. gpt에서.
        if(pdf_file_id):
            delete_gpt_file(pdf_file_id)
        
        # json으로 파싱
        danger_json = json.loads(danger_response)
        fit_json = json.loads(fit_response)
        # 각 데이터를 저장.
        with transaction.atomic():
            danger_report_data_ser = ReportDataSerializer(data=danger_json)
            danger_report_data_ser.is_valid(raise_exception=True)
            danger_report_data_ser.save(report=report)

            fit_report_data_ser = ReportDataSerializer(data=fit_json)
            fit_report_data_ser.is_valid(raise_exception=True)
            fit_report_data_ser.save(report=report)

        # 위험도 레포트 저장.
        return Response([danger_report_data_ser.data, fit_report_data_ser.data], status=status.HTTP_201_CREATED)

# 레포트데이터 dataviewset.
class ReportDataViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/report-data/            -> 전체
    GET /api/report-data/?report=1   -> report_id=1만 필터
    """
    queryset = (ReportData.objects
                .select_related("report")
                .order_by("-created"))
    serializer_class = ReportDataSerializer

    # 검색/정렬/필터
    filterset_fields  = ["report"]              # ?report=1
    ordering_fields   = ["created", "type"]     # ?ordering=type or -created
    
    @extend_schema(
        summary="레포트 데이터 목록",
        description="전체 혹은 report ID로 필터링된 데이터를 반환합니다.",
        tags=["ReportData"],
        responses={200: ReportDataSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="레포트 데이터 상세",
        description="단일 ReportData를 반환합니다.",
        tags=["ReportData"],
        responses={200: ReportDataSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
# 레포트 관련뷰.
class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().order_by("-id")
    serializer_class = ReportSerializer
    
    http_method_names = ["get", "delete"]
    
    @extend_schema(
        summary="레포트 전체",
        description="레포트 전체 목록을 반환합니다.",
        tags=["Report"],
        responses={200: ReportSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="레포트 상세",
        description="특정 레포트 상세를 반환합니다.",
        tags=["Report"],
        responses={200: ReportSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="레포트 삭제",
        description="특정 레포트를 삭제합니다.",
        tags=["Report"],
        responses={
            OpenApiTypes.OBJECT
        },
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return Response(
                {"detail": "다른 객체가 참조 중이라 삭제할 수 없습니다."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

# B) 특정 사용자 리포트 조회: /users/<user_id>/ 요약을 전달한다.
class ReportListByUserView(generics.ListAPIView):
    serializer_class = ReportSummarySerializer

    def get_queryset(self):
        user_id = self.kwargs["user_id"]

        danger_sq = (ReportData.objects
                     .filter(report_id=OuterRef("pk"), type="danger")
                     .order_by("-created")
                     .values("score")[:1])

        fit_sq = (ReportData.objects
                  .filter(report_id=OuterRef("pk"), type="fit")
                  .order_by("-created")
                  .values("score")[:1])

        up = UserPrice.objects.filter(report_id=OuterRef("pk"))
        qs = (Report.objects
              .filter(property_bundle__user_id=user_id)
              .annotate(
                  danger_score=Subquery(danger_sq),
                  fit_score=Subquery(fit_sq),
                  security_deposit=Subquery(up.values("security_deposit")[:1]),
                  monthly_rent=Subquery(up.values("monthly_rent")[:1]),
                  is_year_rent=Subquery(up.values("is_year_rent")[:1]),
              )
              .order_by("-id"))  # ← 여기만 변경

        status_value = self.request.query_params.get("status")
        if status_value:
            qs = qs.filter(status=status_value)
        return qs
