from django.shortcuts import render

# project/apps/testing/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import FloodDepthItemSerializer

from external.client.flood import FloodRiskClient

class FloodDepthProxyView(APIView):
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
