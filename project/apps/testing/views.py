
# project/apps/testing/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# drf-spectacular
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiExample,
)

from .serializers import FloodDepthItemSerializer, FloodDepthResponseSerializer
from external.client.flood import FloodRiskClient


class FloodDepthProxyView(APIView):
    @extend_schema(
        summary="행정구역별 도시침수 심도 통계 조회 (프록시)",
        description=(
            "환경부 한강홍수통제소(get-list_v2) API를 호출해 시도/시군구별 침수 심도 통계를 반환합니다.\n"
            "- 필수: stdgCtpvCd(시도), stdgSggCd(시군구)\n"
            "- 선택: pageNo, numOfRows, fldlvFreq(030/050/080/100), cols, type(json/xml)\n"
        ),
        parameters=[
            OpenApiParameter(name="stdgCtpvCd", type=OpenApiTypes.STR, required=True, description="시도 코드 (예: 11=서울)"),
            OpenApiParameter(name="stdgSggCd",  type=OpenApiTypes.STR, required=True, description="시군구 코드 (예: 680=강남구)"),
            OpenApiParameter(name="pageNo",     type=OpenApiTypes.INT, required=False, description="페이지 번호(기본 1)"),
            OpenApiParameter(name="numOfRows",  type=OpenApiTypes.INT, required=False, description="페이지 크기(기본 10)"),
            OpenApiParameter(name="fldlvFreq",  type=OpenApiTypes.STR, required=False, description="빈도 코드(030/050/080/100)"),
            OpenApiParameter(name="type",       type=OpenApiTypes.STR, required=False, description="응답 타입: json | xml (기본 json)"),
            OpenApiParameter(name="cols",       type=OpenApiTypes.STR, required=False, description="응답 컬럼 지정(쉼표 구분)"),
        ],
        responses={
            200: FloodDepthResponseSerializer,   # ✅ 응답 스키마 명시
            400: OpenApiTypes.OBJECT,
            502: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "성공 예시",
                value={
                    "header": {"resultCode": "0", "resultMsg": "정상"},
                    "items": [
                        {
                            "stdgCtpvCd": "11",
                            "stdgSggCd": "320",
                            "fldlvFreq": "030",
                            "floodAreaDepthLe05": 0.01,
                            "floodAreaDepth0510": 0.02,
                            "floodAreaDepth1020": 0,
                            "floodAreaDepth2050": 0,
                            "floodAreaDepthGt50": 0
                        }
                    ]
                },
            ),
            OpenApiExample(
                "에러 예시(필수 파라미터 누락)",
                value={"detail": "stdgCtpvCd, stdgSggCd는 필수입니다."},
                response_only=True,
                status_codes=["400"],
            ),
        ],
        tags=["Testing / Flood"],  # 문서 그룹핑 표시
    )
    def get(self, request, *args, **kwargs):
        stdg_ctpv_cd = request.query_params.get("stdgCtpvCd")
        stdg_sgg_cd  = request.query_params.get("stdgSggCd")
        if not stdg_ctpv_cd or not stdg_sgg_cd:
            return Response({"detail": "stdgCtpvCd, stdgSggCd는 필수입니다."},
                            status=status.HTTP_400_BAD_REQUEST)

        page_no     = int(request.query_params.get("pageNo", 1))
        num_of_rows = int(request.query_params.get("numOfRows", 10))
        fldlv_freq  = request.query_params.get("fldlvFreq")
        resp_type   = request.query_params.get("type", "json")
        cols        = request.query_params.get("cols")

        client = FloodRiskClient(timeout=20.0)
        try:
            data = client.get_list_v2(
                page_no=page_no,
                num_of_rows=num_of_rows,
                stdg_ctpv_cd=stdg_ctpv_cd,
                stdg_sgg_cd=stdg_sgg_cd,
                fldlv_freq=fldlv_freq,
                resp_type=resp_type,
                cols=cols,
            )
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        finally:
            try:
                client.close()
            except Exception:
                pass

