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
        super().__init__(base_url="http://openapi.seoul.go.kr:8088", timeout=90)
    
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


    def get_realtime_city_air(
            self,
            *,
            size: int = 25,
            gu_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        실시간 대기질(구별) 데이터 조회
        - size: 가져올 레코드 수 (기본 25; 25개 구 전체에 해당)
        - gu_name: 특정 구 이름으로 필터 (예: "강남구"). 한글은 URL 인코딩해서 경로에 붙임.

        반환: JSON(dict) 응답
        예시 필드(일반적): MSRSTE_NM(구명), PM10, PM25, NO2, O3, CO, SO2, IDEX_NM(지수명) 등
        """
        # 1) 기본 경로 구성: /{API_KEY}/json/RealtimeCityAir/1/{size}/
        path = f"/{settings.AIR_QUALITY_KEY}/json/RealtimeCityAir/1/{size}/"

        # 2) 구 이름이 있으면 마지막 경로 세그먼트로 추가 (한글은 URL 인코딩)
        if gu_name:
            path += quote(gu_name)

        # 3) 실제 요청 수행 (BaseClient.get 사용) 및 JSON 반환
        return self.get(path)

    def get_all(self) -> Dict[str, Any]:
        """
        25개 구 전체 최신 측정치(기본 사이즈 25)를 한 번에 가져오는 헬퍼.
        """
        return self.get_realtime_city_air(size=25, gu_name=None)

    def get_air_by_gu(self, gu_name: str) -> Optional[Dict[str, Any]]:
        """
        특정 '구'의 최신 대기질 한 건만 반환.
        - gu_name: "강남구", "마포구" 같은 전체 구명
        반환: dict(한 건) 또는 None(데이터 없음)
        """
        # size=1 로 한 건만 요청
        data = self.get_realtime_city_air(size=1, gu_name=gu_name)

        # 공개 API 응답 스키마: {"RealtimeCityAir": {"row": [ {...}, ... ]}}
        block = data.get("RealtimeCityAir", {}) if isinstance(data, dict) else {}
        rows = block.get("row", [])
        return rows[0] if rows else None

    def get_yearly_average_air_quality(
        self,
        *,
        year: int,                 # MSRDT_YEAR (YYYY)
        start_index: int = 1,      # START_INDEX (정수)
        end_index: int = 25,       # END_INDEX (정수)
        gu_name: Optional[str] = None,  # MSRSTE_NM (선택)
    ) -> Any:
        """
        연평균 대기질(YearlyAverageAirQuality) 조회.
        경로 형태: /{KEY}/json/YearlyAverageAirQuality/{START_INDEX}/{END_INDEX}/{MSRDT_YEAR}/{MSRSTE_NM?}
        """
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
        """특정 연도의 특정 구 연평균 대기질 1건만 반환(없으면 None)."""
        data = self.get_yearly_average_air_quality(
            year=year, start_index=1, end_index=1, gu_name=gu_name
        )
        block = data.get("YearlyAverageAirQuality", {}) if isinstance(data, dict) else {}
        rows = block.get("row", [])
        return rows[0] if rows else None





