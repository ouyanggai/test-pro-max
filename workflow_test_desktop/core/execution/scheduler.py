"""BranchScheduler：分支并发调度 + 失败策略"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Awaitable


logger = logging.getLogger(__name__)


class FailurePolicy(str, Enum):
    STOP_FAILED_BRANCH = "stop_failed_branch"
    STOP_ALL = "stop_all"
    WAIT_ALL_THEN_FAIL = "wait_all_then_fail"


class BranchStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SchedulerResult:
    """调度结果"""
    all_completed: bool
    failed_branches: list[str]
    completed_branches: list[str]
    total_duration_ms: int


@dataclass
class BranchTask:
    branch_key: str
    coroutine: Callable[[], Awaitable]


class BranchScheduler:
    """
    分支并发调度器。

    规则：
    - 流程发起串行（在外部执行）
    - 分支之间并发执行
    - 分支内部节点串行执行
    - 并发上限由 max_concurrency 控制
    - 支持暂停和取消
    """

    def __init__(
        self,
        max_concurrency: int = 5,
        failure_policy: FailurePolicy | str = FailurePolicy.WAIT_ALL_THEN_FAIL,
    ):
        self._max_concurrency = max_concurrency
        self._failure_policy = FailurePolicy(failure_policy)
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._cancel_requested = False
        self._pause_requested = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._branch_status: dict[str, BranchStatus] = {}
        self._results: dict[str, Any] = {}

    def cancel(self) -> None:
        self._cancel_requested = True
        self._pause_event.set()

    def pause(self) -> None:
        self._pause_requested = True
        self._pause_event.clear()

    def resume(self) -> None:
        self._pause_requested = False
        self._pause_event.set()

    async def schedule(
        self,
        branches: list[BranchTask],
        progress_callback: Callable[[str, BranchStatus, Any], None] | None = None,
    ) -> SchedulerResult:
        """调度分支执行，返回调度结果"""
        start_time = time.time()
        failed = []
        completed = []

        async def run_branch(branch: BranchTask) -> None:
            try:
                self._branch_status[branch.branch_key] = BranchStatus.RUNNING
                if progress_callback:
                    progress_callback(branch.branch_key, BranchStatus.RUNNING, None)

                async with self._semaphore:
                    if self._cancel_requested:
                        self._branch_status[branch.branch_key] = BranchStatus.CANCELLED
                        if progress_callback:
                            progress_callback(branch.branch_key, BranchStatus.CANCELLED, None)
                        return

                    await self._pause_event.wait()

                    result = await branch.coroutine()
                    self._results[branch.branch_key] = result
                    self._branch_status[branch.branch_key] = BranchStatus.COMPLETED
                    completed.append(branch.branch_key)
                    if progress_callback:
                        progress_callback(branch.branch_key, BranchStatus.COMPLETED, result)

            except Exception as e:
                logger.exception(f"分支 {branch.branch_key} 执行失败")
                self._branch_status[branch.branch_key] = BranchStatus.FAILED
                failed.append(branch.branch_key)
                if progress_callback:
                    progress_callback(branch.branch_key, BranchStatus.FAILED, str(e))

        await asyncio.gather(*[run_branch(b) for b in branches], return_exceptions=True)

        duration_ms = int((time.time() - start_time) * 1000)

        return SchedulerResult(
            all_completed=len(failed) == 0,
            failed_branches=failed,
            completed_branches=completed,
            total_duration_ms=duration_ms,
        )
