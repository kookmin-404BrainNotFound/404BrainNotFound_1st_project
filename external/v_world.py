# v_world 사이트의 API 요청을 정리.

from external.base import BaseClient
from dotenv import load_dotenv
import os

V_WORLD_KEY = os.getenv("V_WORLD_KEY")

# 주소 검색 API https://www.vworld.kr/dev/v4dv_search2_s001.do

class VWorldClient(BaseClient):
    super.__init__(base_url = 'https://api.vworld.kr/')

    # 주소 검색 함수.
    def search_address(self, query:str):
        params = {
            "request": "search",
            "key": V_WORLD_KEY,
            "format": "json",
            "size": 10,
            "page": 1,
            "query": query,
            "type": "PLACE",
        }
        response = self.get('req/search/', params=params)
        
        return response