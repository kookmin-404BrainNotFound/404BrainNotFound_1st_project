from django.conf import settings
from .base import BaseClient

from external.address.address import Address

from datetime import datetime
settings.SEOUL_DATA_KEY

class DataSeoulClient(BaseClient):
    def __init__(self):
        # 오래 걸리는 작업이라 timeout을 넉넉하게 줌.
        super().__init__(base_url="http://openapi.seoul.go.kr:8088", timeout=90)
    
    # 해당 건물 한정으로 가격을 책정한다. 후에 주변 건물의 가격을 평균내는 로직이 필요할 듯. 이건 다른 함수에 작성.
    def getPrice(
        self,
        size:int = 10,
        year:int = None,
        # 자치구 코드, 법정동코드, 지번구분, 본번 부번 등 생각.
        address:Address = None,
        ):
        # parameter가 아닌 url로 값을 넣는 형태임. 먼저 필수 값들부터 넣는다.
        path = f"/{settings.SEOUL_DATA_KEY}/json/tbLnOpendataRentV/1/{size}/"
        
        path += f"{year}/" if year else "/"
        if address.is_valid():
            path += f"{address.cggCd}/{address.sggNm}/{address.stdgCd}/{address.mtYn}/{address.lnbrMnnm}/{address.lnbrSlno}"

        print(path)
        response = self.get(path)
        return response
