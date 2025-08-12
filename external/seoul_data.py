from django.conf import settings
from .base import BaseClient

settings.SEOUL_DATA_KEY

class DataSeoulClient(BaseClient):
    def __init__(self):
        super().__init__(base_url="http://openapi.seoul.go.kr:8088", timeout=20)
        
    def getPrice(self, size:int = 5):
        # parameter가 아닌 url로 값을 넣는 형태임. 먼저 필수 값들부터 넣고,
        path = f"/{settings.SEOUL_DATA_KEY}/json/tbLnOpendataRentV/1/{size}/"

        response = self.get(path)
        print(response)
        return response