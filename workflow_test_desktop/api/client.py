"""HTTP API 客户端封装（httpx.AsyncClient）

对标 invest 前端 src/utils/axios.js：
- baseURL + path 直接拼接（如 baseURL=/api + path=/web/user/...）
- SID 作为 URL query param ?sid=xxx&platformCode=xxx 和 header sid: xxx 双重发送
- 响应格式：{ isSuccess, data, message } 或 { code, data, message }
"""
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
    - 同时检查 isSuccess / code 业务状态码
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

    @property
    def status_code(self) -> int:
        """直接暴露 HTTP 状态码（供 recorder / executor 使用）"""
        return self._resp.status_code

    @property
    def text(self) -> str:
        """直接暴露原始响应文本（供 recorder 使用）"""
        return self._resp.text


class ApiClient:
    """统一的异步 HTTP 客户端（对标 invest 前端 axios）"""

    def __init__(self, base_url: str, timeout: float = 30.0, sid: str = ""):
        # base_url = "http://192.168.1.220:38081/api"
        # path = "/web/user/api/..." → 完整 URL = base_url + path
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._sid = sid
        self._platform_code = "200001"
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

    def set_platform_code(self, code: str) -> None:
        self._platform_code = code

    def _build_url(self, path: str, params: dict | None) -> tuple[str, dict]:
        """构造完整 URL，SID 注入到 query params（对标 axios interceptor）"""
        url = path
        q = dict(params) if params else {}
        if self._sid:
            # SID 作为 URL query param，对标 invest 前端:
            # url = `${url}?sid=${sid}&platformCode=${platformCode}`
            q["sid"] = self._sid
            q["platformCode"] = self._platform_code
        return url, q

    async def _headers(self, extra: dict | None) -> dict:
        """请求头，SID 也放在 header 中（对标 axios interceptor）"""
        h: dict[str, str] = {"Content-Type": "application/json"}
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
        url, q = self._build_url(path, params)
        resp = await self._client.get(
            url,
            params=q,
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
        url, q = self._build_url(path, None)
        resp = await self._client.post(
            url,
            json=json,
            data=data,
            params=q,
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
        url, q = self._build_url(path, None)
        resp = await self._client.put(
            url,
            json=json,
            params=q,
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
        url, q = self._build_url(path, None)
        resp = await self._client.delete(
            url,
            params=q,
            headers=await self._headers(headers),
        )
        return ApiResponse(resp, path)
