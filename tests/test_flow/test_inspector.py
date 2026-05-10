"""测试 FlowInspector"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from workflow_test_desktop.core.flow.inspector import FlowInspector
from workflow_test_desktop.core.session.lease import SessionLease


@pytest.fixture
def mock_config():
    cfg = MagicMock()
    cfg.flow_detail_path = "/web/flowTemplateApi/detail"
    return cfg


@pytest.fixture
def mock_http():
    mock = MagicMock()
    mock.post = AsyncMock()
    mock.set_sid = MagicMock()
    return mock


@pytest.fixture
def mock_sm():
    mock = MagicMock()
    mock.get_session = AsyncMock(return_value=SessionLease(
        env_id="test", login_type="user_login", username="user1",
        sid="sid_123", generation=1, expires_at=None,
    ))
    return mock


@pytest.fixture
def inspector(mock_config, mock_http, mock_sm):
    return FlowInspector(mock_config, mock_http, mock_sm)


@pytest.mark.asyncio
async def test_inspect_parses_flow(inspector, mock_http, mock_sm):
    """测试完整流程解析"""
    mock_resp = MagicMock()
    # Apifox: /web/flowTemplateApi/detail 返回 ApiResponse 包裹的数据
    mock_resp.json.return_value = {
        "code": 0,
        "message": "ok",
        "data": {
            "flowTemplateId": "flow_001",
            "flowTemplateName": "付款审批",
            "formConfig": [
                {"fieldId": "amount", "label": "金额", "type": "number", "required": True},
                {"fieldId": "reason", "label": "事由", "type": "textarea", "required": False},
            ],
            "flowNodeList": [
                {
                    "nodeId": "node_1",
                    "nodeName": "部门负责人审批",
                    "nodeType": "APPROVAL",
                    "auditType": "ASSIGN",
                    "flowNodeUserList": [
                        {"userId": "user_001", "userName": "张三", "auditType": "assign"},
                    ],
                },
                {
                    "nodeId": "node_2",
                    "nodeName": "财务复核",
                    "nodeType": "APPROVAL",
                    "auditType": "POSITION",
                    "flowNodeUserList": [],
                },
            ],
            "flowBranchList": [
                {"branchId": "branch_main", "branchName": "主线", "parentBranchId": None},
                {"branchId": "branch_parallel", "branchName": "并行分支", "parentBranchId": "branch_main"},
            ],
        }
    }
    mock_http.post = AsyncMock(return_value=mock_resp)

    result = await inspector.inspect("test", "user1", "flow_001")

    assert result.flow_id == "flow_001"
    assert result.flow_name == "付款审批"
    assert len(result.start_form_fields) == 2
    assert result.start_form_fields[0].field_id == "amount"
    assert result.start_form_fields[0].required is True
    assert len(result.branches) == 2
    assert len(result.nodes) == 2
    assert result.nodes[0].requires_assignment is True
    assert result.nodes[1].requires_assignment is False
    assert result.nodes[0].assignment_targets[0].audit_type == "assign"


@pytest.mark.asyncio
async def test_inspect_empty_flow(inspector, mock_http):
    """测试空流程（无分支无节点）"""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "code": 0,
        "data": {
            "flowTemplateId": "flow_empty",
            "flowTemplateName": "空流程",
            "formConfig": [],
            "flowNodeList": [],
            "flowBranchList": [],
        }
    }
    mock_http.post = AsyncMock(return_value=mock_resp)

    result = await inspector.inspect("test", "user1", "flow_empty")
    assert result.flow_name == "空流程"
    assert result.start_form_fields == []
    assert result.branches == []
    assert result.nodes == []
