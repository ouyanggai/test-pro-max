"""FlowCatalogService：按发起账号查询可发起流程"""
from __future__ import annotations

from workflow_test_desktop.core.session.manager import SessionManager
from workflow_test_desktop.core.config.environment import AppConfig
from workflow_test_desktop.data.models import StartableFlow


class FlowCatalogService:
    """
    用发起人 SID 查询可发起流程列表。
    屏蔽后端 API 差异，返回统一的 StartableFlow 列表。
    """

    def __init__(self, config: AppConfig, http_client, session_manager: SessionManager):
        self._config = config
        self._http = http_client
        self._sm = session_manager

    async def list_startable_flows(
        self,
        env_id: str,
        username: str,
        search: str | None = None,
        category: str | None = None,
    ) -> list[StartableFlow]:
        """获取指定账号可发起的流程列表"""
        lease = await self._sm.get_session(env_id, "user_login", username)
        self._http.set_sid(lease.sid)

        body: dict = {"page": 1, "size": 50, "status": "enable"}
        if search:
            body["keyword"] = search
        if category:
            body["flowGroupId"] = category

        resp = await self._http.post(self._config.flow_catalog_path, json=body)
        resp.raise_for_status()
        resp_data = resp.json()
        records = resp_data.get("data", {}).get("records", []) if isinstance(resp_data, dict) else []

        flows = []
        for item in records:
            flows.append(StartableFlow(
                flow_id=item.get("flowTemplateId") or item.get("id", ""),
                flow_code=item.get("flowTemplateCode"),
                flow_name=item.get("flowTemplateName", ""),
                category_name=item.get("flowGroupName"),
                starter_username=username,
                raw=item,
            ))
        return flows
