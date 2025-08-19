from typing import Any, Dict, Optional
import httpx, json

class HTTPError(Exception):
    pass

# Client를 만드는 기본 클래스 구조.
class BaseClient:
    def __init__(self, base_url:str, timeout: float = 5.0):
        self.base_url = base_url
        self.timeout = timeout
        self._client = httpx.Client(base_url=base_url, timeout=timeout)

    def get(self, path:str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            res = self._client.get(path, params=params)
            res.raise_for_status()

            return res.json()
        except httpx.HTTPError as e:
            raise HTTPError(str(e)) from e
    
    def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        is_json: bool = True,
        multipart: bool = False,
    ):
        try:
            if multipart:
                files = {k: (None, str(v)) for k, v in (data or {}).items()}  # <= curl -F와 동일
                res = self._client.post(path, headers=headers, files=files)
            else:
                res = self._client.post(path, data=data, headers=headers)
            res.raise_for_status()

            if is_json:
                try:
                    return res.json()
                except ValueError:
                    ctype = res.headers.get("Content-Type", "")
                    raise HTTPError(f"Expected JSON, got '{ctype}'")
            else:
                return res.content
        except httpx.HTTPError as e:
            raise HTTPError(str(e)) from e
    
    def close(self):
        self._client.close()

