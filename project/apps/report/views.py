from django.core.files.base import ContentFile
from django.http import Http404
from django.db import transaction
from django.utils.decorators import method_decorator
from django.db.models import OuterRef, Subquery

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, viewsets

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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

import json

# Create your views here.

report_id_param = openapi.Parameter(
    name="report_id", in_=openapi.IN_PATH, type=openapi.TYPE_INTEGER,
    description="대상 Report ID", required=True,
)

# 보고서 작성을 시작한다.
class StartReportView(APIView):
    @swagger_auto_schema(
        operation_summary="보고서 시작",
        operation_description="새로운 보고서를 시작합니다.",
        query_serializer=StartReportSerializer
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
    @swagger_auto_schema(
        operation_summary="전월세가 저장",
        operation_description="전월세가 정보를 저장합니다.",
        query_serializer=SaveUserPriceDocSerializer,
        manual_parameters=[report_id_param],
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
    @swagger_auto_schema(
        operation_summary="건축물대장부 저장",
        operation_description="건축물대장부를 저장합니다.",
        manual_parameters=[report_id_param],
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
    @swagger_auto_schema(
        operation_summary="전월세가 평균계산",
        operation_description="전월세가 평균을 계산해 저장합니다.",
        query_serializer=MakeAvgPriceDocSerializer,
        manual_parameters=[report_id_param],
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
    @swagger_auto_schema(
        operation_summary="등기부등본 저장",
        operation_description="등기부등본을 저장합니다.",
        query_serializer=MakeAvgPriceDocSerializer,
        manual_parameters=[report_id_param],
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
    @swagger_auto_schema(
        operation_summary="공기질 데이터 저장.",
        operation_description="공기질 데이터를 저장합니다.",
        manual_parameters=[report_id_param],
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
    @swagger_auto_schema(
        operation_summary="보고서 생성",
        operation_description="보고서를 생성합니다.",
        manual_parameters=[report_id_param],
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
        # system
        system_str = """
        너는 전세사기를 분석하는 전문가야.
        너는 사용자가 제공하는 데이터를 기반으로 위험도 점수, 적합도 점수와 함께
        위험도 레포트, 적합도 레포트를 작성해야 해.
        오직 Json형식으로만 응답하고 이외의 불필요한 텍스트는 모두 제거해줘.
        말투는 진지하게, 수치를 사용자에게 전부 보여주는 방식이 아니라, 축약해서 누구나 알아듣기 쉽게 말로 풀어 설명해줘.
        말투는 항상 ~다.로 끝나게 해줘.
        형식은 다음과 같아.
        [
            {
                "type": "danger",
                "score": "82",
                "description": ""
            },
            {
                "type": "fit",
                "score": "70",
                "description": ""
            }
        ]
        
        각 description은 약 3000자 정도로, 마크다운 문법으로 주고, 이모티콘과 아이콘은 많이 사용하지는 말아줘.

        너가 받을 데이터는 사용자의 보증금과 월세야. 월세가 0이면 전세라고 보면 되는거고. 그게 아니라면 월세라고 판단해.
        그리고 너는 avg로 시작하는 평균 보증금과 월세를 받을 수 있어. 이걸 보고, 전세사기 즉 깡통 전세인지, 월세가 부당한지 등을 판단해.
        그리고 건축물 대장(building_info)에서 문제가 되는 부분이 있으면 언급하고 딱히 문제가 없다면 길게 얘기하지는 마.
        그리고 등기부등본으로 pdf 파일을 받을거야. 그 pdf 파일에서 주의할 점, 문제가 되는 점은 없는지 평가해.

        위 내용들을 종합적으로 평가해서 위험도 점수와 description을 작성하면 돼.

        적합도는 사용자의 성향 데이터와, 건축물대장(building_info), 공기질 데이터, 침수 데이터 등으로 판단해. 절대 마음대로 가정해서 판단하지 말고,
        주어진 데이터를 바탕으로 분석해서 점수를 내주면 돼. 근데 햇빛이나 소음 등은, 사용자의 상세주소와 사는 곳을 바탕으로 추정만 해주고,
        사용자에게 직접 찾아가서 볼 것을 권유해줘.
        그리고 pdf 등이 누락되면 반드시 설명해줘.
        """
        
        messages.append(create_message("system", system_str))
        
        #### 여기부터 위험도 분석 ####
        # 건축물 대장부 등 받기.
        messages.append(create_message("user", str(infos)))
        # gpt에게 등기부등본 보내기.
        if pdf_bytes is not None:
            pdf_file_id = get_gpt_file_id(pdf_bytes, 'gpt-4.1')
            message = create_message("user", [
                {"type": "input_file", "file_id": pdf_file_id},
                {"type": "input_text", "text": "등기부등본 파일이야."}
            ])
            messages.append(message)
        
        # 사용자 성향 데이터 받기.
        messages.append(create_message("user", str(user_tendency)))
        # 공기질 데이터 넣기.
        messages.append(create_message("user", str(air_condiion)))
        # 침수 데이터 넣기.
        messages.append(create_message("user", ""))
        # 분석
        messages.append(create_message("user", "분석해줘."))
        result = ask_gpt(messages, model='gpt-4.1')
        
        # 파일 삭제. gpt에서.
        if(pdf_file_id):
            delete_gpt_file(pdf_file_id)
        
        # json으로 파싱
        data = json.loads(result)
        # 각 데이터를 저장.
        with transaction.atomic():
            danger_report_data_ser = ReportDataSerializer(data=data[0])
            danger_report_data_ser.is_valid(raise_exception=True)
            danger_report_data_ser.save(report=report)

            fit_report_data_ser = ReportDataSerializer(data=data[1])
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
    
    @swagger_auto_schema(
        operation_summary="레포트 데이터 목록",
        operation_description="전체 혹은 report ID로 필터링된 데이터를 반환합니다.",
        tags=["ReportData"],
        responses={200: ReportDataSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="레포트 데이터 상세",
        operation_description="단일 ReportData를 반환합니다.",
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
    
    @swagger_auto_schema(
        operation_summary="레포트 전체",
        operation_description="레포트 전체 목록을 반환합니다.",
        tags=["Report"],
        responses={200: ReportSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="레포트 상세",
        operation_description="특정 레포트 상세를 반환합니다.",
        tags=["Report"],
        responses={200: ReportSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="레포트 삭제",
        operation_description="특정 레포트를 삭제합니다.",
        tags=["Report"],
        responses={
            204: openapi.Response("삭제됨"),
            409: openapi.Response("참조 중이라 삭제 불가(ProtectedError)"),
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
