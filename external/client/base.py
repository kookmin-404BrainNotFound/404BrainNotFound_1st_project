from typing import Any, Dict, Optional
import httpx

class HTTPError(Exception):
    pass

# Client를 만드는 기본 클래스 구조.
class BaseClient:
    def __init__(self, base_url:str, timeout: float = 5.0):
        self.base_url = base_url
        self.timeout = timeout
        self._client = httpx.Client(base_url=base_url, timeout=timeout)

    def get(self, path:str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 우리가 만든 클래스 메서드 이름 / dict를 반환
        try:
            res = self._client.get(path, params=params) # httpx.Client라는 외부 라이브러리의 다른 get 메서드
            res.raise_for_status()

            return res.json()
        except httpx.HTTPError as e:
            raise HTTPError(str(e)) from e
    def close(self):
        self._client.close()

