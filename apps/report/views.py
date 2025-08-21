from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import ReportRun
from .serializers import ReportRunSerializer, SavePriceSerializer

from external.address import building_info
from external.client.a_pick import APickClient
from external.address.price import get_avg_price
from external.address.address import Address
from apps.address.models import TempAddress, TempPrice

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
    def post(self, request, report_run_id):
        try:
            report_run = ReportRun.objects.get(id=report_run_id)
        except ReportRun.DoesNotExist:
            return Response({'error': 'ReportRun not found'}, status=status.HTTP_404_NOT_FOUND)

        # 위험도측정
        # 건축물대장부

        # 전월세가분석

        # 등기부등본분석
        


        # Here you would implement the logic to generate the report        
        return Response({'message': 'Report generated successfully'}, status=status.HTTP_200_OK)