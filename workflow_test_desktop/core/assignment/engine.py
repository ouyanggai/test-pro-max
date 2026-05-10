"""AssignmentEngine：六种指派策略，可复现随机"""
from __future__ import annotations

import random
from workflow_test_desktop.core.assignment.models import (
    AssignmentResult, AssignmentRule, CandidatePool, CandidateScope,
    STRATEGY_MANUAL, STRATEGY_ONE_CLICK, STRATEGY_RANDOM,
    STRATEGY_RANGE_RANDOM, STRATEGY_POSITION_RANDOM,
    STRATEGY_DEPARTMENT_RANDOM,
)


class AssignmentEngine:
    """
    指派引擎。

    输入：候选池 + 策略 + 随机种子
    输出：AssignmentResult（含完整决策信息）

    随机可复现：同一 random_seed + 同一候选池 → 同一结果。
    """

    def assign(
        self,
        rule: AssignmentRule,
        pool: CandidatePool,
        used_ids: set[str],
        starter_username: str | None = None,
        random_seed: int | None = None,
    ) -> AssignmentResult:
        """执行指派"""
        rng = random.Random(random_seed)
        filtered = self._apply_exclusions(pool, rule, used_ids, starter_username)

        if rule.mode == STRATEGY_MANUAL:
            return self._assign_manual(rule, filtered)
        elif rule.mode == STRATEGY_ONE_CLICK:
            return self._assign_one_click(rule, filtered)
        elif rule.mode == STRATEGY_RANDOM:
            return self._random_pick(rule, filtered, rng, random_seed, "随机")
        elif rule.mode == STRATEGY_RANGE_RANDOM:
            return self._random_pick(rule, filtered, rng, random_seed, "范围随机")
        elif rule.mode == STRATEGY_POSITION_RANDOM:
            return self._random_pick(rule, filtered, rng, random_seed, "岗位随机")
        elif rule.mode == STRATEGY_DEPARTMENT_RANDOM:
            return self._random_pick(rule, filtered, rng, random_seed, "部门随机")
        else:
            raise ValueError(f"未知指派模式: {rule.mode}")

    def _apply_exclusions(
        self,
        pool: CandidatePool,
        rule: AssignmentRule,
        used_ids: set[str],
        starter_username: str | None,
    ) -> CandidatePool:
        """应用排除规则到候选池"""
        if rule.selector_type != "user":
            return pool

        scope = rule.scope or CandidateScope()
        users = list(pool.users)

        if scope.exclude_starter and starter_username:
            users = [u for u in users if u.get("username") != starter_username]

        if scope.exclude_used:
            users = [u for u in users if u.get("userId") not in used_ids]

        if scope.users:
            users = [u for u in users if u.get("userId") in scope.users]

        if scope.departments:
            users = [u for u in users if u.get("departmentId") in scope.departments]

        if scope.positions:
            users = [u for u in users if u.get("positionId") in scope.positions]

        if scope.exclude_users:
            users = [u for u in users if u.get("userId") not in scope.exclude_users]

        return CandidatePool(users=users, departments=pool.departments, positions=pool.positions)

    def _assign_manual(self, rule: AssignmentRule, pool: CandidatePool) -> AssignmentResult:
        """手动指定"""
        if rule.selector_type == "user":
            for u in pool.users:
                if u.get("userId") == rule.selected_user:
                    return self._make_result(rule, u.get("userId"), u.get("displayName"),
                                             len(pool.users), None, "手动指定")
        elif rule.selector_type == "department":
            for d in pool.departments:
                if d.get("departmentId") == rule.selected_department:
                    return self._make_result(rule, d.get("departmentId"), d.get("departmentName"),
                                             len(pool.departments), None, "手动指定")
        elif rule.selector_type == "position":
            for p in pool.positions:
                if p.get("positionId") == rule.selected_position:
                    return self._make_result(rule, p.get("positionId"), p.get("positionName"),
                                             len(pool.positions), None, "手动指定")
        raise ValueError(f"手动指定失败：未找到候选人 node={rule.node_id}")

    def _assign_one_click(self, rule: AssignmentRule, pool: CandidatePool) -> AssignmentResult:
        """一键指定：返回第一个候选人"""
        if rule.selector_type == "user" and pool.users:
            u = pool.users[0]
            return self._make_result(rule, u.get("userId"), u.get("displayName"),
                                     len(pool.users), None, "一键指定")
        elif rule.selector_type == "department" and pool.departments:
            d = pool.departments[0]
            return self._make_result(rule, d.get("departmentId"), d.get("departmentName"),
                                     len(pool.departments), None, "一键指定")
        elif rule.selector_type == "position" and pool.positions:
            p = pool.positions[0]
            return self._make_result(rule, p.get("positionId"), p.get("positionName"),
                                     len(pool.positions), None, "一键指定")
        raise ValueError(f"一键指定失败：无候选人 node={rule.node_id}")

    def _random_pick(
        self,
        rule: AssignmentRule,
        pool: CandidatePool,
        rng: random.Random,
        seed: int | None,
        reason: str,
    ) -> AssignmentResult:
        """通用随机选择"""
        if rule.selector_type == "user" and pool.users:
            chosen = rng.choice(pool.users)
            return self._make_result(rule, chosen.get("userId"), chosen.get("displayName"),
                                     len(pool.users), seed, reason)
        elif rule.selector_type == "department" and pool.departments:
            chosen = rng.choice(pool.departments)
            return self._make_result(rule, chosen.get("departmentId"), chosen.get("departmentName"),
                                     len(pool.departments), seed, reason)
        elif rule.selector_type == "position" and pool.positions:
            chosen = rng.choice(pool.positions)
            return self._make_result(rule, chosen.get("positionId"), chosen.get("positionName"),
                                     len(pool.positions), seed, reason)
        raise ValueError(f"随机失败：无候选人 node={rule.node_id}")

    def _make_result(
        self,
        rule: AssignmentRule,
        selected_id: str,
        selected_name: str,
        candidate_count: int,
        random_seed: int | None,
        reason: str,
    ) -> AssignmentResult:
        return AssignmentResult(
            node_id=rule.node_id,
            field=rule.field,
            selector_type=rule.selector_type,
            mode=rule.mode,
            selected_id=selected_id,
            selected_name=selected_name,
            candidate_count=candidate_count,
            random_seed=random_seed,
            reason=reason,
            candidate_snapshot_id=None,
        )
