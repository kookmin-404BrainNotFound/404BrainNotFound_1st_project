# apps/testing/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from external.client.flood import FloodRiskClient
from .serializers import FloodDepthResponseSerializer, MessageSerializer

class FloodDepthProxyView(APIView):
    @extend_schema(
        summary="행정구역별 도시침수 심도 통계 조회 (프록시)",
        description="환경부(한강홍수통제소) get-list_v2 호출",
        parameters=[
            OpenApiParameter(name="stdgCtpvCd", type=OpenApiTypes.STR,
                             location=OpenApiParameter.QUERY, required=True,
                             description="시도코드(예: 11=서울)"),
            OpenApiParameter(name="stdgSggCd",  type=OpenApiTypes.STR,
                             location=OpenApiParameter.QUERY, required=True,
                             description="시군구코드(예: 680=강남구)"),
            OpenApiParameter(name="pageNo",     type=OpenApiTypes.INT,
                             location=OpenApiParameter.QUERY, required=False,
                             description="페이지 번호(기본 1)"),
            OpenApiParameter(name="numOfRows",  type=OpenApiTypes.INT,
                             location=OpenApiParameter.QUERY, required=False,
                             description="페이지 크기(기본 10)"),
            OpenApiParameter(name="fldlvFreq",  type=OpenApiTypes.STR,
                             location=OpenApiParameter.QUERY, required=False,
                             description="빈도코드(030/050/080/100)"),
            OpenApiParameter(name="type",       type=OpenApiTypes.STR,
                             location=OpenApiParameter.QUERY, required=False,
                             description="응답 타입 json|xml(기본 json)"),
            # OpenApiParameter(name="cols",       type=OpenApiTypes.STR,
            #                  location=OpenApiParameter.QUERY, required=False,
            #                  description="응답 컬럼 지정(쉼표)"),
        ],
        responses={200: FloodDepthResponseSerializer, 400: MessageSerializer, 502: MessageSerializer},
        tags=["testing"],
    )
    def get(self, request, *args, **kwargs):
        stdg_ctpv_cd = request.query_params.get("stdgCtpvCd")
        stdg_sgg_cd  = request.query_params.get("stdgSggCd")
        if not stdg_ctpv_cd or not stdg_sgg_cd:
            return Response({"detail": "stdgCtpvCd, stdgSggCd는 필수입니다."}, status=400)

        # 숫자 변환은 400으로 처리
        try:
            page_no     = int(request.query_params.get("pageNo", 1))
            num_of_rows = int(request.query_params.get("numOfRows", 10))
        except (TypeError, ValueError):
            return Response({"detail": "pageNo/numOfRows는 정수여야 합니다."}, status=400)

        fldlv_freq = request.query_params.get("fldlvFreq") or "030"  # 기본값 권장
        resp_type  = request.query_params.get("type", "json")
        # cols       = request.query_params.get("cols")
        cols_param = request.query_params.get("cols", None)
        if cols_param:
            cols_param = ",".join([c.strip() for c in cols_param.split(",") if c.strip()])
        else:
            cols_param = None


        client = FloodRiskClient(timeout=20.0)
        try:
            data = client.get_list_v2(
                page_no=page_no,
                num_of_rows=num_of_rows,
                stdg_ctpv_cd=stdg_ctpv_cd,
                stdg_sgg_cd=stdg_sgg_cd,
                fldlv_freq=fldlv_freq,
                resp_type=resp_type,
                cols=cols_param
            )
            return Response(data, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=502)
        finally:
            try: client.close()
            except Exception: pass
