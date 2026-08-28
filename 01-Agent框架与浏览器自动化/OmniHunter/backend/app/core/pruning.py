"""攻击树动态剪枝策略：避免无效算力浪费。

用户优化建议：攻击树不要生成完就全量跑，做动态调度。
  1) 生成时按「成功率 + 危害等级」排序，优先跑高价值分支
  2) 执行中设置失败阈值：同类请求连续失败 N 次，剪掉该整条分支
  3) 命中即停：发现一个高危漏洞，记录后暂停该方向测试，优先验证其他维度

本模块给 Attacker / Specialist 调用，控制攻击动作执行节奏。
"""
from typing import Any


class PruningPolicy:
    """攻击树剪枝策略 + 执行状态跟踪。"""

    def __init__(self, max_consecutive_failures: int = 3,
                 stop_on_high_severity: bool = True,
                 stop_on_critical: bool = True):
        # 阈值
        self.max_consecutive_failures = max_consecutive_failures
        self.stop_on_high_severity = stop_on_high_severity
        self.stop_on_critical = stop_on_critical

        # 执行状态
        self._branch_failures: dict[str, int] = {}  # branch_id -> 连续失败数
        self._pruned_branches: set[str] = set()       # 已剪掉的分支
        self._high_vuln_found_branches: set[str] = set()  # 已命中高危的分支
        self._stopped = False  # 全局停止（发现 critical）

    def should_execute(self, branch_id: str, leaf_id: str = "") -> bool:
        """判断该叶子动作是否应执行。"""
        if self._stopped:
            return False
        if branch_id in self._pruned_branches:
            return False
        # 命中过该分支高危，且开启 stop_on_high，跳过该分支后续
        if (self.stop_on_high_severity
                and branch_id in self._high_vuln_found_branches):
            return False
        return True

    def record_failure(self, branch_id: str) -> None:
        """记录一次失败，达到阈值剪枝。"""
        self._branch_failures[branch_id] = \
            self._branch_failures.get(branch_id, 0) + 1
        if self._branch_failures[branch_id] >= self.max_consecutive_failures:
            self._pruned_branches.add(branch_id)

    def record_success(self, branch_id: str) -> None:
        """记录一次成功（重置失败计数）。"""
        self._branch_failures[branch_id] = 0

    def record_vuln_found(self, branch_id: str, severity: str) -> None:
        """记录发现漏洞，按 severity 决定是否暂停该分支/全局。"""
        sev = severity.lower()
        if sev in ("high", "critical"):
            self._high_vuln_found_branches.add(branch_id)
        if sev == "critical" and self.stop_on_critical:
            self._stopped = True

    def stats(self) -> dict[str, Any]:
        return {
            "pruned_branches": list(self._pruned_branches),
            "high_vuln_branches": list(self._high_vuln_found_branches),
            "stopped_globally": self._stopped,
            "branch_failures": dict(self._branch_failures),
        }


def prioritize_actions(actions: list[dict]) -> list[dict]:
    """按成功率 + 危害等级排序攻击动作（优先跑高价值分支）。

    每个 action 含 success_rate (0-1) + severity (info/low/medium/high/critical)。
    排序公式: score = success_rate * 0.4 + severity_weight * 0.6
    """
    sev_weight = {"critical": 1.0, "high": 0.8, "medium": 0.5,
                  "low": 0.3, "info": 0.1}
    scored = []
    for a in actions:
        sr = float(a.get("success_rate", 0.5) or 0.5)
        sv = sev_weight.get(str(a.get("severity", "medium")).lower(), 0.5)
        score = sr * 0.4 + sv * 0.6
        scored.append((score, a))
    # 按分数降序
    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored]
