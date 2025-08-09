# v_world 사이트의 API 요청을 정리.

from external.base import BaseClient
from dotenv import load_dotenv
import os

V_WORLD_KEY = os.getenv("V_WORLD_KEY")

# 주소 검색 API https://www.vworld.kr/dev/v4dv_search2_s001.do

class VWorldClient(BaseClient):
    def __init__(self):
        super().__init__(base_url='https://api.vworld.kr/')

    # 주소 검색 함수.
    def search_address(self, query:str, size:int = 10, page: int = 1):
        params = {
            "service": "search",
            "version": "2.0",
            "request": "search",
            "key": V_WORLD_KEY,
            "format": "json",
            "errorformat": "json",
            "size": size,
            "page": page,
            "query": query,
            "type": "PLACE",
        }
        response = self.get('req/search/', params=params)
        
        return response