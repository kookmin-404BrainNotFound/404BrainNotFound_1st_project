from __future__ import annotations

import json
import os, sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))  # .../project
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

#.env 로드 (프로젝트 루트의 .env 파일)
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    dotenv_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
except Exception:
    # dotenv 미설치/오류 시에도 아래에서 settings/환경변수로 계속 시도
    pass

from external.client.base import BaseClient, HTTPError
from django.conf import settings
from typing import Any, Dict, List, Optional, Union


"""
환경부 한강홍수통제소 - 행정구역별 도시침수 지도 침수심 통계 조회 (get-list_v2)
문서: data.go.kr 서비스 ID 15141718
엔드포인트 베이스: https://apis.data.go.kr/14809064/InquireAdmCtyFLService_v2
"""

# --- 서비스키 로딩: settings → 환경변수(.env 로드 결과) 순 ---
# 통일: DATA_GO_KR_DECODING_KEY
FLOOD_SERVICE_KEY: Optional[str] = None
try:
    if getattr(settings, "configured", False):
        FLOOD_SERVICE_KEY = getattr(settings, "DATA_GO_KR_DECODING_KEY", None)
except Exception:
    # settings 미초기화 상태면 그냥 넘어감
    pass

if not FLOOD_SERVICE_KEY:
    FLOOD_SERVICE_KEY = os.environ.get("DATA_GO_KR_DECODING_KEY")  # .env 로드 결과가 여기에 들어옴


class FloodRiskClient(BaseClient):
    def __init__(self, timeout: float = 20.0):
        super().__init__(
            base_url="https://apis.data.go.kr/14809064/InquireAdmCtyFLService_v2",
            timeout=timeout,
        )

    def get_list_v2(
        self,
        *,
        page_no: int = 1,
        num_of_rows: int = 10,
        stdg_ctpv_cd: Optional[str] = None,   # 시도 코드
        stdg_sgg_cd: Optional[str] = None,    # 시군구 코드
        fldlv_freq: Optional[str] = None,     # 빈도 구분 (예: "030")
        cols: Optional[str] = None,           # 응답 컬럼 지정 (쉼표로 분리)
        resp_type: str = "json",              # "json" | "xml"
        service_key: Optional[str] = None,    # 기본: DATA_GO_KR_DECODING_KEY
    ) -> Dict[str, Any]:
        """
        GET get-list_v2  (주의: 앞에 슬래시 붙이지 않음)

        반환 예시(JSON):
        {
          "response": {
            "header": {"resultCode":"0","resultMsg":"정상"},
            "body": {
              "items": {
                "item": [
                  {
                    "stdgCtpvCd":"11", "stdgSggCd":"320", "fldlvFreq":"030",
                    "floodAreaDepthLe05": 0.01,
                    "floodAreaDepth0501e": 0.02,
                    "floodAreaDepth1020": 0,
                    "floodAreaDepth2050": 0,
                    "floodAreaDepthGt50": 0
                  }
                ]
              }
            }
          }
        }
        """
        key = service_key or FLOOD_SERVICE_KEY
        if not key:
            raise HTTPError(
                "서비스키가 없습니다. settings.DATA_GO_KR_DECODING_KEY 또는 "
                "환경변수 DATA_GO_KR_DECODING_KEY (.env 포함) 를 설정하세요."
            )

        params: Dict[str, Union[str, int]] = {
            "serviceKey": key,
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "type": resp_type,
        }
        if stdg_ctpv_cd:
            params["stdgCtpvCd"] = stdg_ctpv_cd
        if stdg_sgg_cd:
            params["stdgSggCd"] = stdg_sgg_cd
        if fldlv_freq:
            params["fldlvFreq"] = fldlv_freq
        if cols:
            params["cols"] = cols

        #절대경로가 아니라 상대경로 문자열로 전달 (앞에 슬래시 금지)
        data = self.get("get-list_v2", params=params)

        # 안전한 파싱
        resp = data.get("response", {}) if isinstance(data, dict) else {}
        header = resp.get("header", {})
        result_code = str(header.get("resultCode", ""))
        if result_code != "0":
            raise HTTPError(f"API error: {result_code} - {header.get('resultMsg')}")

        items_block = resp.get("body", {}).get("items", {})
        items = items_block.get("item", [])
        if isinstance(items, dict):  # 단일 객체로 오는 케이스 대비
            items = [items]

        return {"header": header, "items": items}

    def get_by_codes(
        self,
        *,
        stdg_ctpv_cd: str,
        stdg_sgg_cd: str,
        fldlv_freq: Optional[str] = None,
        cols: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """시도/시군구 기준 1페이지 조회 후 item 리스트만 반환."""
        result = self.get_list_v2(
            page_no=1,
            num_of_rows=10,
            stdg_ctpv_cd=stdg_ctpv_cd,
            stdg_sgg_cd=stdg_sgg_cd,
            fldlv_freq=fldlv_freq,
            cols=cols,
        )
        return result["items"]







