"""HTTP API 客户端封装（httpx.AsyncClient）"""
from __future__ import annotations

import httpx


class ApiClient:
    """统一的异步 HTTP 客户端"""

    def __init__(self, base_url: str, timeout: float = 30.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> ApiClient:
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args) -> None:
        if self._client:
            await self._client.aclose()

    def set_sid(self, sid: str) -> None:
        """注入 SID 到请求头"""
        if self._client:
            self._client.headers["X-SID"] = sid

    async def get(
        self,
        path: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> httpx.Response:
        if not self._client:
            raise RuntimeError("ApiClient not entered")
        merged_headers = dict(self._client.headers)
        if headers:
            merged_headers.update(headers)
        return await self._client.get(path, params=params, headers=merged_headers)

    async def post(
        self,
        path: str,
        json: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> httpx.Response:
        if not self._client:
            raise RuntimeError("ApiClient not entered")
        merged_headers = dict(self._client.headers)
        if headers:
            merged_headers.update(headers)
        return await self._client.post(path, json=json, data=data, headers=merged_headers)

    async def put(
        self,
        path: str,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> httpx.Response:
        if not self._client:
            raise RuntimeError("ApiClient not entered")
        merged_headers = dict(self._client.headers)
        if headers:
            merged_headers.update(headers)
        return await self._client.put(path, json=json, headers=merged_headers)

    async def delete(
        self,
        path: str,
        headers: dict | None = None,
    ) -> httpx.Response:
        if not self._client:
            raise RuntimeError("ApiClient not entered")
        merged_headers = dict(self._client.headers)
        if headers:
            merged_headers.update(headers)
        return await self._client.delete(path, headers=merged_headers)
