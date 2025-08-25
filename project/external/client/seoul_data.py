from django.conf import settings
from .base import BaseClient, HTTPError

from external.address.address_manager import AddressManager

from typing import Any, Dict, Optional
from urllib.parse import quote


"""
서울 열린데이터 광장 API 클라이언트
  - 전월세( tbLnOpendataRentV )
  - 실시간 대기질( RealtimeCityAir )
"""

class DataSeoulClient(BaseClient):
    def __init__(self):
        # 오래 걸리는 작업이라 timeout을 넉넉하게 줌, 8088 포트 http 사용
        super().__init__(base_url="http://openapi.seoul.go.kr:8088", timeout=120)
    
    # 해당 건물 한정으로 가격을 책정한다. 후에 주변 건물의 가격을 평균내는 로직이 필요할 듯. 이건 다른 함수에 작성.
    def getPrice(
        self,
        size:int = 10,
        page:int = 1,
        year:int = None,
        # 자치구 코드, 법정동코드, 지번구분, 본번 부번 등 생각.
        address:AddressManager = None,
        ):
        # parameter가 아닌 url로 값을 넣는 형태임. 먼저 필수 값들부터 넣는다.
        path = f"/{settings.SEOUL_DATA_KEY}/json/tbLnOpendataRentV/{page}/{size}/"
        
        path += f"{year}/" if year else "/"
        if address and address.is_valid(): # ← address가 None이면 AttributeError
            path += f"{address.cggCd}/{address.sggNm}/{address.stdgCd}/{address.mtYn}/{address.lnbrMnnm}/{address.lnbrSlno}"

        response = self.get(path)
        return response

    def get_yearly_average_air_quality(
        self,
        *,
        year: int,                 # MSRDT_YEAR (YYYY)
        start_index: int = 1,      # START_INDEX (정수)
        end_index: int = 25,       # END_INDEX (정수)
        gu_name: Optional[str] = None,  # MSRSTE_NM (선택)
    ) -> Any:
        segs = [
            settings.AIR_QUALITY_KEY,
            "json",
            "YearlyAverageAirQuality",
            str(start_index),
            str(end_index),
            str(year),
        ]
        path = "/" + "/".join(segs) + "/"
        if gu_name:  # 선택 세그먼트
            path += quote(gu_name)
        return self.get(path)

    def get_yearly_by_gu(self, year: int, gu_name: str) -> Optional[dict]:
        data = self.get_yearly_average_air_quality(
            year=year, start_index=1, end_index=1, gu_name=gu_name
        )
        block = data.get("YearlyAverageAirQuality", {}) if isinstance(data, dict) else {}
        rows = block.get("row", [])
        return rows[0] if rows else None





