"""测试 NodeExecutor"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from workflow_test_desktop.core.execution.executor import NodeExecutor, NodeStatus
from workflow_test_desktop.core.session.lease import SessionLease
from workflow_test_desktop.core.assignment.models import AssignmentResult
from workflow_test_desktop.data.models import FlowNodeDescriptor


def make_mock_response(status_code: int, body_dict: dict) -> MagicMock:
    """生成一个行为类似 httpx.Response 的 MagicMock，json() 返回真实 dict"""
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = json.dumps(body_dict, ensure_ascii=False)
    mock.json = lambda: body_dict
    return mock


@pytest.fixture
def mock_session_manager():
    mock = MagicMock()
    mock.get_session = AsyncMock(return_value=SessionLease(
        env_id="test",
        login_type="user_login",
        username="handler1",
        sid="mock_sid_xyz",
        generation=1,
        expires_at=None,
    ))
    mock.refresh_if_needed = AsyncMock(return_value=SessionLease(
        env_id="test",
        login_type="user_login",
        username="handler1",
        sid="mock_sid_xyz",
        generation=1,
        expires_at=None,
    ))
    return mock


@pytest.fixture
def mock_recorder():
    mock = MagicMock()
    mock.log_request = AsyncMock()
    mock.log_response = AsyncMock()
    return mock


@pytest.fixture
def mock_http():
    mock = MagicMock()
    mock.set_sid = MagicMock()
    mock.post = AsyncMock()
    return mock


@pytest.fixture
def executor(mock_session_manager, mock_recorder, mock_http):
    return NodeExecutor(mock_session_manager, mock_recorder, mock_http)


@pytest.fixture
def sample_node():
    return FlowNodeDescriptor(
        node_id="node_1",
        node_name="部门审批",
        node_type="APPROVAL",
        audit_type="ASSIGN",
        branch_id="branch_1",
        requires_assignment=True,
        assignment_targets=[],
        raw={},
    )


@pytest.fixture
def sample_assignment():
    return AssignmentResult(
        node_id="node_1",
        field="approver",
        selector_type="user",
        mode="manual",
        selected_id="handler1",
        selected_name="处理人1",
        candidate_count=1,
        random_seed=None,
        reason="手动指定",
    )


@pytest.mark.asyncio
async def test_execute_success(executor, mock_session_manager, mock_recorder, mock_http,
                                sample_node, sample_assignment):
    """节点执行成功，audit_type=APPROVE"""
    mock_resp = make_mock_response(200, {"code": 0, "message": "ok"})
    mock_http.post = AsyncMock(return_value=mock_resp)

    result = await executor.execute(
        node_run_id="nr_001",
        node=sample_node,
        assignment=sample_assignment,
        execution_id="1",
        branch_id="br_001",
        env_id="test",
        flow_instance_id="fi_001",
        job_task_link_id="jtl_001",
        action_type="APPROVE",
        comment="同意",
    )

    assert result["status"] == "completed"
    assert result["handler"] == "handler1"
    assert result["node_id"] == "node_1"
    mock_recorder.log_request.assert_called_once()
    mock_recorder.log_response.assert_called_once()
    # 验证 SID 被设置
    mock_http.set_sid.assert_called_once_with("mock_sid_xyz")
    # 验证 POST 调用
    mock_http.post.assert_called_once()
    call_args = mock_http.post.call_args
    assert call_args.kwargs["json"]["flowInstanceId"] == "fi_001"
    assert call_args.kwargs["json"]["auditType"] == "APPROVE"


@pytest.mark.asyncio
async def test_execute_without_assignment_returns_failed(executor, mock_session_manager, sample_node):
    """无指派结果时返回 failed 状态（ValueError 被捕获）"""
    mock_session_manager.get_session = AsyncMock()

    result = await executor.execute(
        node_run_id="nr_002",
        node=sample_node,
        assignment=None,
        execution_id="1",
        branch_id="br_001",
        env_id="test",
        flow_instance_id="fi_001",
        job_task_link_id="jtl_001",
    )

    assert result["status"] == "failed"
    assert "无法解析处理人" in result["error"]


@pytest.mark.asyncio
async def test_execute_http_error_then_relogin_retry(executor, mock_session_manager, mock_http,
                                                       sample_node, sample_assignment):
    """HTTP 请求失败后触发重登，重登后重试成功"""
    # 第一次失败；重登后返回新 SID，第二次成功
    mock_ok = make_mock_response(200, {"code": 0, "message": "ok"})
    mock_http.post = AsyncMock(side_effect=[Exception("network error"), mock_ok])

    # refresh_if_needed 返回新 lease（新 SID）
    new_lease = SessionLease(
        env_id="test",
        login_type="user_login",
        username="handler1",
        sid="new_sid_after_relogin",
        generation=2,
        expires_at=None,
    )
    mock_session_manager.refresh_if_needed = AsyncMock(return_value=new_lease)

    result = await executor.execute(
        node_run_id="nr_003",
        node=sample_node,
        assignment=sample_assignment,
        execution_id="1",
        branch_id="br_001",
        env_id="test",
        flow_instance_id="fi_001",
        job_task_link_id="jtl_001",
    )

    # 两次 POST 调用
    assert mock_http.post.call_count == 2
    # 新 SID 被设置
    assert mock_http.set_sid.call_count == 2
    assert mock_http.set_sid.call_args_list[1][0][0] == "new_sid_after_relogin"


@pytest.mark.asyncio
async def test_execute_reject(executor, mock_http, sample_node, sample_assignment):
    """REJECT 操作"""
    mock_resp = make_mock_response(200, {"code": 0, "message": "ok"})
    mock_http.post = AsyncMock(return_value=mock_resp)

    result = await executor.execute(
        node_run_id="nr_004",
        node=sample_node,
        assignment=sample_assignment,
        execution_id="2",
        branch_id="br_001",
        env_id="test",
        flow_instance_id="fi_001",
        job_task_link_id="jtl_001",
        action_type="REJECT",
        comment="驳回",
    )

    assert result["status"] == "completed"
    call_args = mock_http.post.call_args
    assert call_args.kwargs["json"]["auditType"] == "REJECT"


@pytest.mark.asyncio
async def test_execute_pause_blocks(executor, mock_session_manager, mock_recorder, mock_http,
                                      sample_node, sample_assignment):
    """暂停时节点执行被阻塞"""
    executor.pause()

    async def check_paused():
        # 在 0.05s 后恢复
        await asyncio.sleep(0.05)
        executor.resume()

    mock_resp = make_mock_response(200, {"code": 0})
    mock_http.post = AsyncMock(return_value=mock_resp)

    async def run_with_pause():
        task = asyncio.create_task(executor.execute(
            node_run_id="nr_005",
            node=sample_node,
            assignment=sample_assignment,
            execution_id="1",
            branch_id="br_001",
            env_id="test",
            flow_instance_id="fi_001",
            job_task_link_id="jtl_001",
        ))
        await asyncio.sleep(0.02)
        executor.resume()
        return await task

    result = await asyncio.gather(
        run_with_pause(),
    )
    assert result[0]["status"] == "completed"


@pytest.mark.asyncio
async def test_node_status_constants():
    """NodeStatus 枚举值正确"""
    assert NodeStatus.PENDING == "pending"
    assert NodeStatus.RUNNING == "running"
    assert NodeStatus.COMPLETED == "completed"
    assert NodeStatus.FAILED == "failed"
    assert NodeStatus.SKIPPED == "skipped"


@pytest.mark.asyncio
async def test_execute_builds_correct_request_body(executor, mock_http, sample_node,
                                                    sample_assignment):
    """验证构造的请求体字段正确"""
    mock_resp = make_mock_response(200, {"code": 0})
    mock_http.post = AsyncMock(return_value=mock_resp)

    await executor.execute(
        node_run_id="nr_006",
        node=sample_node,
        assignment=sample_assignment,
        execution_id="3",
        branch_id="br_001",
        env_id="test",
        flow_instance_id="fi_xyz",
        job_task_link_id="jtl_xyz",
        action_type="APPROVE",
        comment="测试意见",
    )

    call_args = mock_http.post.call_args
    body = call_args.kwargs["json"]
    assert body["flowInstanceId"] == "fi_xyz"
    assert body["jobTaskLinkId"] == "jtl_xyz"
    assert body["auditType"] == "APPROVE"
    assert body["comment"] == "测试意见"
