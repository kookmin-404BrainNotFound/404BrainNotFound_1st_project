# buisiness.juso 사이트의 API 요청을 정리.
from external.address.address_manager import AddressManager

from .base import BaseClient
from django.conf import settings

# 건축물대장 정보 조회 등이 포함됨. address 객체는 이미 search가 끝난 상태라고 가정한다.(initialize.)
class DataGoKrClient(BaseClient):
    def __init__(self, address:AddressManager = None):
        super().__init__(base_url='https://apis.data.go.kr/')
        self.address = address
        self.basic_params = {
            "serviceKey": settings.DATA_GO_KR_DECODING_KEY,
            "sigunguCd": address.cggCd,
            "bjdongCd": address.stdgCd,
            "bun": address.lnbrMnnm,
            "ji": address.lnbrSlno,
            "_type": "json",
        }
    # 건축HUB 건축물대장 표제부 조회.
    def getBuildingAPI(self, path='/getBrTitleInfo'):
        response = self.get(f"1613000/BldRgstHubService{path}", params=self.basic_params)
        
        return response