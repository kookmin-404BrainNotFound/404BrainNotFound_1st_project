from .base import BaseClient
from django.conf import settings


class APickClient(BaseClient):
    def __init__(self):
        super().__init__(base_url='https://apick.app/rest/', timeout=2000)

    # 주소 검색 함수.
    def view_property_registry(self, full_addr:str, unique_num=None, type_="집합건물"):
        headers = {"CL_AUTH_KEY": settings.A_PICK_KEY}
        data = {
            "address": full_addr,
            "unique_num": unique_num,
            "type": type_,
        }
        # None 제거.
        data = {k: v for k, v in data.items() if v is not None}

        response = self.post("iros/1", data=data, headers=headers, is_json=True, multipart=True)

        return response

    def download_property_registry(self, ic_id:int, *, format="pdf", stream=False):
        headers = {
            "CL_AUTH_KEY": settings.A_PICK_KEY,
        }

        data = {
            "ic_id": ic_id,
            "format": format,
        }

        pdf_bytes = self.post(
            "iros_download/1",
            data=data,
            headers=headers,
            is_json=False,
            multipart=True,
        )

        return pdf_bytes
