"""测试 BranchScheduler"""
import pytest
import asyncio
from workflow_test_desktop.core.execution.scheduler import (
    BranchScheduler, BranchTask, FailurePolicy, BranchStatus, SchedulerResult,
)


@pytest.fixture
def scheduler():
    return BranchScheduler(max_concurrency=2, failure_policy=FailurePolicy.WAIT_ALL_THEN_FAIL)


@pytest.mark.asyncio
async def test_all_branches_complete(scheduler):
    """所有分支成功完成"""
    async def make_branch(key: str, delay: float):
        await asyncio.sleep(delay)
        return f"result_{key}"

    branches = [
        BranchTask(branch_key=f"b{i}", coroutine=lambda i=i: make_branch(f"b{i}", 0.05))
        for i in range(1, 4)
    ]

    result = await scheduler.schedule(branches)

    assert result.all_completed is True
    assert len(result.completed_branches) == 3
    assert result.failed_branches == []


@pytest.mark.asyncio
async def test_failed_branch_reported(scheduler):
    """失败分支被正确记录"""
    async def failing_task():
        raise RuntimeError("模拟失败")

    async def success_task():
        await asyncio.sleep(0.01)
        return "ok"

    branches = [
        BranchTask(branch_key="success", coroutine=success_task),
        BranchTask(branch_key="fail", coroutine=failing_task),
    ]

    result = await scheduler.schedule(branches)

    assert result.all_completed is False
    assert "fail" in result.failed_branches
    assert "success" in result.completed_branches


@pytest.mark.asyncio
async def test_max_concurrency_limit():
    """并发上限生效"""
    scheduler = BranchScheduler(max_concurrency=2)
    max_concurrent = 0
    current_concurrent = 0

    async def track_task():
        nonlocal current_concurrent, max_concurrent
        current_concurrent += 1
        max_concurrent = max(max_concurrent, current_concurrent)
        await asyncio.sleep(0.05)
        current_concurrent -= 1

    branches = [BranchTask(branch_key=f"b{i}", coroutine=track_task) for i in range(4)]

    await scheduler.schedule(branches)
    assert max_concurrent <= 2


@pytest.mark.asyncio
async def test_cancel_stops_pending_branches():
    """取消请求停止待执行分支"""
    scheduler = BranchScheduler(max_concurrency=1)

    async def long_task():
        await asyncio.sleep(10)

    branches = [
        BranchTask(branch_key="c1", coroutine=long_task),
        BranchTask(branch_key="c2", coroutine=long_task),
    ]

    async def cancel_after_ms():
        await asyncio.sleep(0.03)
        scheduler.cancel()

    await asyncio.gather(
        scheduler.schedule(branches),
        cancel_after_ms(),
    )

    statuses = list(scheduler._branch_status.values())
    assert BranchStatus.CANCELLED in statuses or BranchStatus.RUNNING in statuses


@pytest.mark.asyncio
async def test_pause_and_resume(scheduler):
    """暂停和恢复控制"""
    events = []

    async def pausable_task():
        events.append("start")
        await asyncio.sleep(0.05)
        events.append("end")

    branches = [
        BranchTask(branch_key="p1", coroutine=pausable_task),
        BranchTask(branch_key="p2", coroutine=pausable_task),
    ]

    async def pause_then_resume():
        await asyncio.sleep(0.01)
        scheduler.pause()
        await asyncio.sleep(0.05)
        scheduler.resume()

    await asyncio.gather(
        scheduler.schedule(branches),
        pause_then_resume(),
    )

    assert "start" in events
    assert "end" in events


@pytest.mark.asyncio
async def test_result_captured_per_branch():
    """每个分支结果被正确捕获"""
    async def task_with_result(value):
        await asyncio.sleep(0.01)
        return {"value": value}

    branches = [
        BranchTask(branch_key="r1", coroutine=lambda: task_with_result("x")),
        BranchTask(branch_key="r2", coroutine=lambda: task_with_result("y")),
    ]

    scheduler = BranchScheduler(max_concurrency=2)
    result = await scheduler.schedule(branches)

    assert scheduler._results["r1"]["value"] == "x"
    assert scheduler._results["r2"]["value"] == "y"


@pytest.mark.asyncio
async def test_failure_policy_enum():
    """FailurePolicy 枚举值正确"""
    assert FailurePolicy.WAIT_ALL_THEN_FAIL.value == "wait_all_then_fail"
    assert FailurePolicy.STOP_ALL.value == "stop_all"
    assert FailurePolicy.STOP_FAILED_BRANCH.value == "stop_failed_branch"


@pytest.mark.asyncio
async def test_branch_status_enum():
    """BranchStatus 枚举值正确"""
    assert BranchStatus.PENDING.value == "pending"
    assert BranchStatus.RUNNING.value == "running"
    assert BranchStatus.COMPLETED.value == "completed"
    assert BranchStatus.FAILED.value == "failed"
    assert BranchStatus.CANCELLED.value == "cancelled"


@pytest.mark.asyncio
async def test_empty_branches():
    """空分支列表返回空结果"""
    scheduler = BranchScheduler()
    result = await scheduler.schedule([])
    assert result.all_completed is True
    assert result.completed_branches == []
    assert result.failed_branches == []
