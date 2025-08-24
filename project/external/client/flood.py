from __future__ import annotations

import json

import os
from typing import Any, Dict, List, Optional

from django.conf import settings
from external.client.base import BaseClient, HTTPError  # 경로는 프로젝트에 맞게

class FloodRiskClient(BaseClient):
    #올바른 베이스 URL
    BASE_URL = "https://apis.data.go.kr/1480964/InquireAdmCtyFLService_v2/"

    def __init__(self, timeout: float = 20.0):

        key = (getattr(settings, "DATA_GO_KR_DECODING_KEY", "") or
               os.getenv("DATA_GO_KR_DECODING_KEY", "")).strip()
        if not key:
            raise ValueError("DATA_GO_KR_DECODING_KEY 가 비어 있습니다.")

        # BaseClient 초기화
        super().__init__(base_url=self.BASE_URL, timeout=timeout)

        # 나중에 재사용할 서비스키 저장
        self.service_key = key

    def get_list_v2(
        self,
        page_no: int = 1,
        num_of_rows: int = 10,
        stdg_ctpv_cd: str | None = None,
        stdg_sgg_cd: str | None = None,
        fldlv_freq: str | None = None,
        resp_type: str = "json",
        cols: str | None = None,
    ) -> Dict[str, Any]:
        """get-list_v2 원본 응답(JSON dict)을 그대로 반환."""
        if not stdg_ctpv_cd or not stdg_sgg_cd:
            raise ValueError("stdgCtpvCd, stdgSggCd 는 필수입니다.")

        params: Dict[str, Any] = {
            "serviceKey": self.service_key,
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "stdgCtpvCd": stdg_ctpv_cd,
            "stdgSggCd": stdg_sgg_cd,
        }
        if fldlv_freq:
            params["fldlvFreq"] = fldlv_freq
        if cols:
            params["cols"] = cols  # 문자열이어야 함 (예: "col1,col2")

        # 1차: type
        try:
            return self.get("get-list_v2", params={**params, "type": (resp_type or "json")})
        except HTTPError:
            # 2차 폴백: resultType (일부 서비스 명칭 차이 대응)
            return self.get("get-list_v2", params={**params, "resultType": (resp_type or "json")})

    def get_by_codes(
        self,
        *,
        stdg_ctpv_cd: str,
        stdg_sgg_cd: str,
        fldlv_freq: Optional[str] = None,
        cols: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """시도/시군구 기준 1페이지 조회 후 item 리스트만 반환."""
        data = self.get_list_v2(
            page_no=1,
            num_of_rows=10,
            stdg_ctpv_cd=stdg_ctpv_cd,
            stdg_sgg_cd=stdg_sgg_cd,
            fldlv_freq=fldlv_freq,
            # cols=cols,
        )
        # 외부 응답 구조에 맞춰 키 접근
        return data.get("items", data)  # 안전하게 처리



