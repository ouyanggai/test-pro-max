"""Assignment engine"""
from workflow_test_desktop.core.assignment.engine import AssignmentEngine
from workflow_test_desktop.core.assignment.models import (
    AssignmentRule, AssignmentResult, CandidatePool, CandidateScope,
    STRATEGY_MANUAL, STRATEGY_ONE_CLICK, STRATEGY_RANDOM,
    STRATEGY_RANGE_RANDOM, STRATEGY_POSITION_RANDOM,
    STRATEGY_DEPARTMENT_RANDOM,
)

__all__ = [
    "AssignmentEngine",
    "AssignmentRule", "AssignmentResult", "CandidatePool", "CandidateScope",
    "STRATEGY_MANUAL", "STRATEGY_ONE_CLICK", "STRATEGY_RANDOM",
    "STRATEGY_RANGE_RANDOM", "STRATEGY_POSITION_RANDOM",
    "STRATEGY_DEPARTMENT_RANDOM",
]
