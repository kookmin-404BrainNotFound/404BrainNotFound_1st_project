from __future__ import annotations
from typing import Any, Dict, Optional
import httpx, json, certifi, ssl


class HTTPError(Exception):
    pass

# Client를 만드는 기본 클래스 구조.
class BaseClient:
    def __init__(self, base_url:str, timeout: float = 20.0):
        self.base_url = base_url
        self.timeout = timeout
        
        ctx = ssl.create_default_context(cafile=certifi.where())
        try:
            ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
        except ssl.SSLError:
            pass
        
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            http2=False,
            verify=ctx,
            trust_env=False,
            follow_redirects=True,
        )

    def get(self, path:str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 우리가 만든 클래스 메서드 이름 / dict를 반환
        try:
            res = self._client.get(path, params=params) # httpx.Client라는 외부 라이브러리의 다른 get 메서드
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

