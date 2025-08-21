from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import ReportRun
from .serializers import ReportRunSerializer, SavePriceSerializer, MakeReportSerializer

from external.address.building_info import BuildingInfo
from external.address.price import get_avg_price
from external.address.address import Address
from external.address.property_registry import get_property_registry
from apps.address.models import TempAddress, TempPrice

from external.gpt.gpt_manager import *

import json

# Create your views here.

class StartReportView(APIView):
    @swagger_auto_schema(
        operation_summary="보고서 시작",
        operation_description="새로운 보고서를 시작합니다.",
        query_serializer=ReportRunSerializer
    )
    def post(self, request):
        serializer = ReportRunSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        report_run = ReportRun.objects.create()

        # 주소 검색 및 Address 객체 만들기.
        vd = serializer.validated_data
        address = Address(roadAddr=vd["road_address"])
        address.initialize(research=True)
        if not address.is_valid():
            return Response({"error": "유효하지 않은 주소입니다."}, status=status.HTTP_400_BAD_REQUEST)
        address.details = vd.get("details", "")

         # 모델 필드명에 맞춰 저장 (road_addr)
        temp_address = TempAddress.objects.create(
            report_run=report_run,            
            road_address=address.roadAddr,
            bd_nm=address.bdNm,
            adm_cd=address.admCd,
            sgg_nm=address.sggNm,
            mt_yn=address.mtYn,
            lnbr_mnnm=address.lnbrMnnm,
            lnbr_slno=address.lnbrSlno,
            details=address.details,
        )

        # 응답은 원시 타입/딕셔너리만
        return Response(
            {
                "report_run_id": report_run.id,
                "temp_address_id": temp_address.id,
                "address": {
                    "road_addr": address.roadAddr,
                    "bd_nm": address.bdNm,
                    "adm_cd": address.admCd,
                    "sgg_nm": address.sggNm,
                    "mt_yn": address.mtYn,
                    "lnbr_mnnm": address.lnbrMnnm,
                    "lnbr_slno": address.lnbrSlno,
                    "details": address.details,
                },
            },
            status=status.HTTP_201_CREATED,
        )
    
# 전월세가 임시 저장.
class SavePriceView(APIView):
    @swagger_auto_schema(
        operation_summary="전월세가 저장",
        operation_description="전월세가 정보를 저장합니다.",
        query_serializer=SavePriceSerializer
    )
    def post(self, request):
        serializer = SavePriceSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        report_run_id = serializer.validated_data["report_run_id"]
        try:
            report_run = ReportRun.objects.get(id=report_run_id)
        except ReportRun.DoesNotExist:
            return Response({'error': 'ReportRun not found'}, status=status.HTTP_404_NOT_FOUND)

        # 가격 저장
        temp_price = TempPrice.objects.create(
            report_run=report_run,
            security_deposit=serializer.validated_data.get("security_deposit"),
            monthly_rent=serializer.validated_data.get("monthly_rent")
        )

        return Response({"temp_price_id": temp_price.id}, status=status.HTTP_201_CREATED)

class MakeReportView(APIView):
    @swagger_auto_schema(
        operation_summary="보고서 생성",
        operation_description="보고서를 생성합니다.",
        query_serializer=MakeReportSerializer
    )
    def post(self, request):
        serializer = MakeReportSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        report_run_id = vd["report_run_id"]
        try:
            report_run = ReportRun.objects.get(id=report_run_id)
        except ReportRun.DoesNotExist:
            return Response({'error': 'ReportRun not found'}, status=status.HTTP_404_NOT_FOUND)

        # 위험도측정
        # 주소 만들기.
        address = Address(
            roadAddr=report_run.temp_address.road_address,
            bdNm=report_run.temp_address.bd_nm,
            admCd=report_run.temp_address.adm_cd,
            sggNm=report_run.temp_address.sgg_nm,
            mtYn=report_run.temp_address.mt_yn,
            lnbrMnnm=report_run.temp_address.lnbr_mnnm,
            lnbrSlno=report_run.temp_address.lnbr_slno,
            details=report_run.temp_address.details
        )
        address.initialize(research=False)

        # 건축물대장부
        building_info = BuildingInfo().makeInfo(address)
        # 전월세가분석
        price_info = get_avg_price(
            startYear=vd.get("startYear", 2024),
            address=address
        )
        # user의 전월세가
        user_price_info = {
            "security_deposit": report_run.temp_prices.security_deposit,
            "monthly_rent": report_run.temp_prices.monthly_rent
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
                pdf_data = get_property_registry(full_addr=address.roadAddr + " " + address.details)
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
        messages.append(create_message("user", json.dumps(infos)))
        messages.append(create_message("user", "분석해줘."))

        result = ask_gpt(messages)
        print(result)
        return Response(result)