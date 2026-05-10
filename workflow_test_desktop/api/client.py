"""HTTP API 客户端封装（httpx.AsyncClient）"""
from __future__ import annotations

import httpx


class ApiError(Exception):
    """API 调用异常（人类可读）"""

    def __init__(self, http_status: int, path: str, message: str, detail: str = ""):
        self.http_status = http_status
        self.path = path
        self.message = message
        self.detail = detail
        super().__init__(message)

    def __str__(self) -> str:
        if self.http_status == 0:
            return f"无法连接服务器（{self.message}）"
        if self.http_status == 401:
            return "认证失败：登录已过期，请重新打开应用"
        if self.http_status == 403:
            return "无权限访问此接口"
        if self.http_status >= 500:
            return f"服务器错误（{self.http_status}）：{self.message}"
        return self.message


class ApiResponse:
    """
    API 响应包装器。
    - 自动解析 JSON，失败时抛 ApiError
    - 自动检查 HTTP 状态码，非 2xx 抛 ApiError
    """

    def __init__(self, resp: httpx.Response, path: str):
        self._resp = resp
        self._path = path
        self._data: dict | None = None

    def json(self) -> dict:
        """解析 JSON，失败时抛 ApiError"""
        if self._data is not None:
            return self._data

        status = self._resp.status_code
        body = self._resp.text.strip()

        # 非 2xx HTTP 状态
        if status < 200 or status >= 300:
            hint = ""
            if status == 404:
                hint = "接口地址不存在，请检查配置"
            elif status == 401:
                hint = "认证失败"
            elif status == 403:
                hint = "无权限"
            elif status >= 500:
                hint = "服务器内部错误"
            raise ApiError(
                http_status=status,
                path=self._path,
                message=hint or f"HTTP {status}",
                detail=body[:500] if body else "",
            )

        # 空响应
        if not body:
            raise ApiError(
                http_status=status,
                path=self._path,
                message="服务器返回空响应",
            )

        # 非 JSON
        if not body.startswith("{"):
            raise ApiError(
                http_status=status,
                path=self._path,
                message=f"服务器返回非JSON格式（长度 {len(body)} 字节）",
                detail=body[:200],
            )

        try:
            self._data = self._resp.json()
        except Exception as e:
            raise ApiError(
                http_status=status,
                path=self._path,
                message="响应JSON解析失败",
                detail=f"{body[:200]}\n\n解析错误: {e}",
            )

        return self._data


class ApiClient:
    """统一的异步 HTTP 客户端"""

    def __init__(self, base_url: str, timeout: float = 30.0, sid: str = ""):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._sid = sid
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
        self._sid = sid

    async def _headers(self, extra: dict | None) -> dict:
        h = {"Content-Type": "application/json"}
        if self._sid:
            h["sid"] = self._sid
        if extra:
            h.update(extra)
        return h

    async def get(
        self,
        path: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> ApiResponse:
        if not self._client:
            raise RuntimeError("ApiClient not entered")
        resp = await self._client.get(
            path,
            params=params,
            headers=await self._headers(headers),
        )
        return ApiResponse(resp, path)

    async def post(
        self,
        path: str,
        json: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> ApiResponse:
        if not self._client:
            raise RuntimeError("ApiClient not entered")
        resp = await self._client.post(
            path,
            json=json,
            data=data,
            headers=await self._headers(headers),
        )
        return ApiResponse(resp, path)

    async def put(
        self,
        path: str,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> ApiResponse:
        if not self._client:
            raise RuntimeError("ApiClient not entered")
        resp = await self._client.put(
            path,
            json=json,
            headers=await self._headers(headers),
        )
        return ApiResponse(resp, path)

    async def delete(
        self,
        path: str,
        headers: dict | None = None,
    ) -> ApiResponse:
        if not self._client:
            raise RuntimeError("ApiClient not entered")
        resp = await self._client.delete(
            path,
            headers=await self._headers(headers),
        )
        return ApiResponse(resp, path)
