"""Execution engine"""
from workflow_test_desktop.core.execution.run_plan import RunPlan, RunPlanBuilder

__all__ = [
    "RunPlan", "RunPlanBuilder",
    "BranchScheduler", "BranchTask", "FailurePolicy", "BranchStatus", "SchedulerResult",
    "NodeExecutor", "NodeStatus",
    "ExecutionController",
]


def __getattr__(name: str):
    if name in (
        "BranchScheduler", "BranchTask", "FailurePolicy", "BranchStatus", "SchedulerResult",
    ):
        from workflow_test_desktop.core.execution.scheduler import (
            BranchScheduler, BranchTask, FailurePolicy, BranchStatus, SchedulerResult,
        )
        return locals()[name]
    if name in ("NodeExecutor", "NodeStatus"):
        from workflow_test_desktop.core.execution.executor import NodeExecutor, NodeStatus
        return locals()[name]
    if name == "ExecutionController":
        from workflow_test_desktop.core.execution.controller import ExecutionController
        return ExecutionController
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
