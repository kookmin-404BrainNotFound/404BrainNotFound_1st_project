from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Report
from .serializers import StartReportSerializer, SaveUserPriceSerializer, MakeReportSerializer, MakeAvgPriceReportSerializer

from external.address.building_info import BuildingInfoManager
from external.address.price import get_avg_price
from external.address.address_manager import AddressManager
from external.address.property_registry import get_property_registry
from apps.address.models import Address, UserPrice, BuildingInfo, AvgPrice

from external.gpt.gpt_manager import *

import json

# Create your views here.

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
        # 새 report 객체 생성.
        report = Report.objects.create()

        # 주소 검색 및 Address 객체 만들기.
        vd = serializer.validated_data
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
        query_serializer=SaveUserPriceSerializer
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
class MakeBuildingInfoReportView(APIView):
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
class MakeAvgPriceReportView(APIView):
    @swagger_auto_schema(
        operation_summary="전월세가 평균계산",
        operation_description="전월세가 평균을 계산해 저장합니다.",
        query_serializer=MakeAvgPriceReportSerializer
    )
    def post(self, request, report_id):
        serializer = MakeAvgPriceReportSerializer(data=request.query_params)
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

# 마지막 레포트 뷰. gpt에게 맡기는 역할만 수행.
class MakeReportFinalView(APIView):
    @swagger_auto_schema(
        operation_summary="보고서 생성",
        operation_description="보고서를 생성합니다.",
        query_serializer=MakeReportSerializer
    )
    def post(self, request, report_id):
        serializer = MakeReportSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({'error': 'ReportRun not found'}, status=status.HTTP_404_NOT_FOUND)

        # 위험도측정
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
        # 등기부등본
        pdf_data = None
        if vd.get("is_property_registry", False):
            try:
                pdf_data = get_property_registry(full_addr=address_manager.roadAddr + " " + address_manager.details)
            except Exception as e:
                pdf_data = None
        
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
        messages.append(create_message("user", str(infos)))
        messages.append(create_message("user", "분석해줘."))
        result = ask_gpt(messages, model='gpt-4.1')
        return Response(result)