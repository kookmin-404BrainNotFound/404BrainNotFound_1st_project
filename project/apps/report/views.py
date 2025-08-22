from django.core.files.base import ContentFile
from django.http import Http404
from django.db import transaction
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.users.models import User


from .models import Report, ReportData
from .serializers import StartReportSerializer, SaveUserPriceSerializer, MakeAvgPriceSerializer, ReportDataSerializer, ReportSerializer

from external.address.building_info import BuildingInfoManager
from external.address.price import get_avg_price
from external.address.address_manager import AddressManager
from external.address.property_registry import get_property_registry
from apps.address.serializers import PropertyRegistrySerializer
from apps.address.models import Address, UserPrice, BuildingInfo, AvgPrice, PropertyRegistry

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
            return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)

        # 새 report 객체 생성.
        report = Report.objects.create(user=user)

        # 주소 검색 및 Address 객체 만들기.
        address_manager = AddressManager(roadAddr=vd["road_address"])
        address_manager.initialize(research=True)
        if not address_manager.is_valid():
            return Response({"error": "유효하지 않은 주소입니다."}, status=status.HTTP_400_BAD_REQUEST)
        address_manager.details = vd.get("details", "")

        # 모델 필드명에 맞춰 저장 (road_addr)
        address = Address.objects.create(
            report=report,            
            road_address=address_manager.roadAddr,
            bd_nm=address_manager.bdNm,
            adm_cd=address_manager.admCd,
            sgg_nm=address_manager.sggNm,
            mt_yn=address_manager.mtYn,
            lnbr_mnnm=address_manager.lnbrMnnm,
            lnbr_slno=address_manager.lnbrSlno,
            details=address_manager.details,
        )

        # 응답은 원시 타입/딕셔너리만
        return Response(
            {
                "report_id": report.id,
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
        query_serializer=SaveUserPriceSerializer,
        manual_parameters=[report_id_param],
        tags=["report_danger"],
    )
    def post(self, request, report_id):
        serializer = SaveUserPriceSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)

        # 가격 저장
        user_price = UserPrice.objects.create(
            report=report,
            security_deposit=serializer.validated_data.get("security_deposit"),
            monthly_rent=serializer.validated_data.get("monthly_rent"),
            is_year_rent=serializer.validated_data.get("is_year_rent"),
        )

        return Response({"user_price_id": user_price.id}, status=status.HTTP_201_CREATED)

# 건축물대장부 가져오기.
class MakeBuildingInfoView(APIView):
    @swagger_auto_schema(
        operation_summary="건축물대장부 저장",
        operation_description="축물대장부를 저장합니다.",
        manual_parameters=[report_id_param],
        tags=["report_danger"],
    )
    def post(self, request, report_id):
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # 주소 가져오기.
        address_manager:AddressManager = report.address.to_address_manager()
        address_manager.initialize(research=False)
        
        # 건축물대장부
        info = BuildingInfoManager().makeInfo(address_manager)
        building_info = BuildingInfo.objects.create(
            report=report,
            description=str(info),
        )
        
        return Response({"building_info_id": building_info.id, "building_info": str(info)}, status=status.HTTP_201_CREATED)

# 전월세가 평균 계산하기.
class MakeAvgPriceView(APIView):
    @swagger_auto_schema(
        operation_summary="전월세가 평균계산",
        operation_description="전월세가 평균을 계산해 저장합니다.",
        query_serializer=MakeAvgPriceSerializer,
        manual_parameters=[report_id_param],
        tags=["report_danger"],
    )
    def post(self, request, report_id):
        serializer = MakeAvgPriceSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # 주소 가져오기.
        address_manager:AddressManager = report.address.to_address_manager()
        address_manager.initialize(research=False)
        
        # 전월세가분석
        price_info = get_avg_price(
            startYear=vd.get("start_year", 2024),
            address_manager=address_manager
        )
        
        # 저장하기
        avg_price = AvgPrice.objects.create(
            report=report,
            avg_year_price=price_info["avg_year_price"],
            avg_month_security_price=price_info["avg_month_security_price"],
            avg_month_rent=price_info["avg_month_rent"],
        )
        
        return Response({"avg_price_id": avg_price.id, "price_info": str(price_info)})

# 등기부등본 조회뷰.
class MakePropertyRegistryView(APIView):
    @swagger_auto_schema(
        operation_summary="등기부등본 저장",
        operation_description="등기부등본을 저장합니다.",
        query_serializer=MakeAvgPriceSerializer,
        manual_parameters=[report_id_param],
        tags=["report_danger"],
    )
    def post(self, request, report_id):
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # 주소 가져오기.
        address_manager:AddressManager = report.address.to_address_manager()
        address_manager.initialize(research=False)
        
        # 등기부등본 조회하기.
        full_addr = address_manager.getFullAddr()
        pdf_bytes = get_property_registry(full_addr=full_addr)
        print(full_addr)
        filename = "등기부등본.pdf"
        
        property_registry = PropertyRegistry(report=report)
        property_registry.pdf.save(filename, ContentFile(pdf_bytes), save=True)
        
        serializer = PropertyRegistrySerializer(property_registry, context={"request":request})
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        
####### 적합도 시작 ########

        
        
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

        ##### 위험도측정 ##### 
        # 주소 만들기
        address_manager:AddressManager = report.address.to_address_manager()
        address_manager.initialize(research=False)
                
        # 건축물대장부 그냥 string으로 가져온다.
        building_info = report.building_info.description
        # 전월세가분석
        avg_price:AvgPrice = report.avg_price
        price_info = {
            "avg_year_price": avg_price.avg_year_price,
            "avg_month_security_price": avg_price.avg_month_security_price,
            "avg_month_rent": avg_price.avg_month_rent,
        }
        # user의 전월세가
        user_price:UserPrice = report.user_price
        user_price_info = {
            "security_deposit": user_price.security_deposit,
            "monthly_rent": user_price.monthly_rent,
            "is_year_rent": user_price.is_year_rent,
        }

        # 파일을 제외한 dict
        infos = {
            "building_info": building_info,
            "user_price_info": user_price_info,
            "price_info": price_info,
        }
        # 등기부등본 있으면 가져오기.
        pdf_bytes = None
        try:
            pr = PropertyRegistry.objects.select_related("report").get(report_id=report_id)
            with pr.pdf.open("rb") as f:
                pdf_bytes = f.read()
        except PropertyRegistry.DoesNotExist:
            pdf_bytes = None
            
        ##################
        
        ##### 적합도 측정 #####
        
        
        # gpt에 물어본다. 처음에는 파일을 제외하고, 파일까지 첨부한 후 물어본다.
        messages = []
        # system
        system_str = """
        너는 전세사기를 분석하는 전문가야.
        너는 사용자가 제공하는 데이터를 기반으로 위험도 점수, 적합도 점수와 함께
        위험도 레포트, 적합도 레포트를 작성해야 해.
        오직 Json형식으로만 응답하고 이외의 불필요한 텍스트는 모두 제거해줘.
        형식은 다음과 같아.
        {
            "danger_score": "82",
            "danger_description": "",
            "fit_score": "70",
            "fit_description": ""
        }
        
        각 description은 약 3000자 정도로, 마크다운 문법으로 주고, 이모티콘과 아이콘은 많이 사용하지는 말아줘.

        너가 받을 데이터는 사용자의 보증금과 월세야. 월세가 0이면 전세라고 보면 되는거고. 그게 아니라면 월세라고 판단해.
        그리고 너는 avg로 시작하는 평균 보증금과 월세를 받을 수 있어. 이걸 보고, 전세사기 즉 깡통 전세인지, 월세가 부당한지 등을 판단해.
        그리고 건축물 대장(building_info)에서 문제가 되는 부분이 있으면 언급하고 딱히 문제가 없다면 길게 얘기하지는 마.
        그리고 등기부등본으로 pdf 파일을 받을거야. 그 pdf 파일에서 주의할 점, 문제가 되는 점은 없는지 평가해.

        위 내용들을 종합적으로 평가해서 위험도 점수와 description을 작성하면 돼.

        적합도는 일단 3000자를 채우지 말고, 점수도 그냥 0으로 설정해. 나중에 내가 다시 이 부분에 대해 설명해줄거야.
        그리고 pdf 등이 누락되면 반드시 설명해줘.
        """
        
        messages.append(create_message("system", system_str))
        
        #### 여기부터 위험도 분석 ####
        messages.append(create_message("user", str(infos)))
        # gpt에게 등기부등본 보내기.
        if pdf_bytes is not None:
            file_id = get_gpt_file_id(pdf_bytes, 'gpt-4.1')
            message = create_message("user", [
                {"type": "input_file", "file_id": file_id},
                {"type": "input_text", "text": "등기부등본 파일이야."}
            ])
            messages.append(message)
            
        messages.append(create_message("user", "분석해줘."))
        result = ask_gpt(messages, model='gpt-4.1')
        
        # 파일 삭제.
        delete_gpt_file(file_id)
        
        # json으로 파싱
        data = json.loads(result)
        
        # 위험도 레포트 저장.
        return save_danger_and_fit(request, report, data)

def save_danger_and_fit(request, report, payload: dict):
    """
    payload 예:
    {
      "danger_score": "23",
      "danger_description": "...",
      "fit_score": "0",
      "fit_description": ""
    }
    """
    # 점수 캐스팅 (문자열 들어와도 안전)
    def to_int(val, default=0):
        try:
            return int(val)
        except (TypeError, ValueError):
            return default

    danger_score = to_int(payload.get("danger_score", 0))
    fit_score    = to_int(payload.get("fit_score", 0))

    danger_description = payload.get("danger_description", "") or ""
    fit_description    = payload.get("fit_description", "") or ""

    def upsert(kind: str, score: int, description: str):
        base_data = {
            "report": report.id,
            "score": score,
            "description": description,
            "type": kind,  # "danger" or "fit"
        }
        instance = ReportData.objects.filter(report=report, type=kind).first()
        if instance:
            serializer = ReportDataSerializer(instance, data=base_data, partial=True, context={"request": request})
        else:
            serializer = ReportDataSerializer(data=base_data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return ReportDataSerializer(obj, context={"request": request}).data

    with transaction.atomic():
        danger_data = upsert("danger", danger_score, danger_description)
        fit_data    = upsert("fit",    fit_score,    fit_description)

    # 두 결과를 함께 반환
    return Response(
        {"danger": danger_data, "fit": fit_data},
        status=status.HTTP_201_CREATED
    )
    
@method_decorator(name="get", decorator=swagger_auto_schema(
    operation_summary="전체 레포트 GET",
    operation_description="전체 레포트 데이터를 가져옵니다.",
    tags=["ReportData"],
    responses={200: ReportDataSerializer(many=True)},
))
# 1) 전체 목록: /report-data/
class ReportDataListAllView(generics.ListAPIView):
    queryset = ReportData.objects.select_related("report").order_by("-created")
    serializer_class = ReportDataSerializer


@method_decorator(name="get", decorator=swagger_auto_schema(
    operation_summary="레포트 GET",
    operation_description="특정 레포트 데이터를 가져옵니다.",
    tags=["ReportData"],
    manual_parameters=[report_id_param],
    responses={200: ReportDataSerializer(many=True)},
))
class ReportDataByReportView(generics.ListAPIView):
    serializer_class = ReportDataSerializer

    def get_queryset(self):
        report_id = self.kwargs["report_id"]
        return (ReportData.objects
                .select_related("report")
                .filter(report_id=report_id)
                .order_by("type", "-created"))

# Report에서 필요한 부분들만 가져옵니다. ReportData가 언제 만들어졌는지, 주소, 위험도/적합도 점수, 사용자 UserPrice 등.
class ReportDetailedSummaryView(APIView):
    @swagger_auto_schema(
        operation_summary="레포트에서 필요한 부분만을 가져옵니다.",
        operation_description="주소, 생성날짜, 월세/전세 여부, 가격, 주소",
        manual_parameters=[report_id_param],
    )
    def get(self, request, report_id):
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # 주소 가져오기.
        address_manager:AddressManager = report.address.to_address_manager()
        address_manager.initialize(research=False)
        
        result = {
            "road_address": address_manager.roadAddr,
            "created_at": report.created_at,
            "danger_score": report.report_data.filter(type='danger').values_list('score', flat=True).first(),
            "fit_score": report.report_data.filter(type='fit').values_list('score', flat=True).first(),
            "is_year": report.user_price.is_year_rent,
            "security_deposit": report.user_price.security_deposit,
            "monthly_rent": report.user_price.monthly_rent,
        }
        
        return Response(result, status=status.HTTP_201_CREATED)



# A) 모든 리포트 조회: /reports/
class ReportListAllView(generics.ListAPIView):
    serializer_class = ReportSerializer

    def get_queryset(self):
        qs = Report.objects.all().order_by("-created_at")
        status_value = self.request.query_params.get("status")
        if status_value:
            qs = qs.filter(status=status_value)
        return qs

    @swagger_auto_schema(
        operation_summary="모든 리포트 조회",
        operation_description="전체 Report 목록을 반환합니다. status 쿼리로 필터링 가능.",
        responses={200: openapi.Response("OK", ReportSerializer(many=True))}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# B) 특정 사용자 리포트 조회: /users/<user_id>/reports/
class ReportListByUserView(generics.ListAPIView):
    serializer_class = ReportSerializer

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        qs = Report.objects.filter(user_id=user_id).order_by("-created_at")
        status_value = self.request.query_params.get("status")
        if status_value:
            qs = qs.filter(status=status_value)
        return qs

    @swagger_auto_schema(
        operation_summary="특정 사용자 리포트 조회",
        operation_description="user_id에 해당하는 사용자의 Report 목록을 반환합니다. status 쿼리로 필터링 가능.",
        responses={200: openapi.Response("OK", ReportSerializer(many=True))}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)