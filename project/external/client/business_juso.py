# buisiness.juso 사이트의 API 요청을 정리.

from .base import BaseClient
from django.conf import settings

# 주소 검색 API https://www.vworld.kr/dev/v4dv_search2_s001.do

class BusinessJusoClient(BaseClient):
    def __init__(self):
        super().__init__(base_url='https://business.juso.go.kr/')

    # 주소 검색 함수.
    def search_address(self, query:str, size:int = 10, page: int = 1):
        params = {
            "confmKey":settings.BUSINESS_JUSO_KEY,
            "currentPage":page,
            "countPerPage":size,
            "keyword":query,
            "resultType":"json",
        }
        response = self.get('addrlink/addrLinkApi.do', params=params)
        
        return response