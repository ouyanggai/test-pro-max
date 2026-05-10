"""测试 FlowCatalogService"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from workflow_test_desktop.core.flow.catalog import FlowCatalogService
from workflow_test_desktop.core.session.lease import SessionLease


@pytest.fixture
def mock_config():
    cfg = MagicMock()
    cfg.gateway_url = "https://api.example.com"
    cfg.flow_catalog_path = "/web/flowTemplateApi/list"
    return cfg


@pytest.fixture
def mock_http_client():
    mock = MagicMock()
    mock.post = AsyncMock()
    mock.set_sid = MagicMock()
    return mock


@pytest.fixture
def mock_session_manager():
    mock = MagicMock()
    mock.get_session = AsyncMock(return_value=SessionLease(
        env_id="test", login_type="user_login", username="user1",
        sid="mock_sid_123", generation=1, expires_at=None,
    ))
    return mock


@pytest.fixture
def catalog_service(mock_config, mock_http_client, mock_session_manager):
    return FlowCatalogService(mock_config, mock_http_client, mock_session_manager)


@pytest.mark.asyncio
async def test_list_startable_flows(catalog_service, mock_http_client, mock_session_manager):
    """测试正常查询流程"""
    mock_resp = MagicMock()
    # Apifox: PageResponse格式 {"code": 0, "data": {"records": [...]}}
    mock_resp.json.return_value = {
        "code": 0,
        "data": {
            "records": [
                {"flowTemplateId": "flow_001", "flowTemplateName": "付款审批", "flowGroupName": "财务"},
                {"flowTemplateId": "flow_002", "flowTemplateName": "请假申请", "flowGroupName": "HR"},
            ],
            "total": 2,
            "page": 1,
            "size": 10,
        }
    }
    mock_http_client.post = AsyncMock(return_value=mock_resp)

    flows = await catalog_service.list_startable_flows("test", "user1")

    assert len(flows) == 2
    assert flows[0].flow_id == "flow_001"
    assert flows[0].flow_name == "付款审批"
    assert flows[1].flow_id == "flow_002"
    mock_session_manager.get_session.assert_called_once_with("test", "user_login", "user1")
    mock_http_client.set_sid.assert_called_with("mock_sid_123")


@pytest.mark.asyncio
async def test_list_startable_flows_with_filter(catalog_service, mock_http_client):
    """测试带搜索和分类过滤"""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"code": 0, "data": {"records": [], "total": 0, "page": 1, "size": 10}}
    mock_http_client.post = AsyncMock(return_value=mock_resp)

    await catalog_service.list_startable_flows("test", "user1", search="付款", category="财务")

    mock_http_client.post.assert_called_once()
    call_args = mock_http_client.post.call_args
    # POST body 中 keyword 和 flowGroupId
    assert call_args.kwargs["json"]["keyword"] == "付款"
    assert call_args.kwargs["json"]["flowGroupId"] == "财务"
