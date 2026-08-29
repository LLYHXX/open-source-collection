"""CVSS 3.1 基础定级（Base Score）—— 验证通过的漏洞自动打分定级。

支持完整 Base 向量解析与计算（AV/AC/PR/UI/S/C/I/A），
插件只需给 vector 字符串，调度器统一算分并映射 severity。
"""
from __future__ import annotations

import math

_AV = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}
_AC = {"L": 0.77, "H": 0.44}
_PR_UNCHANGED = {"N": 0.85, "L": 0.62, "H": 0.27}
_PR_CHANGED = {"N": 0.85, "L": 0.68, "H": 0.5}
_UI = {"N": 0.85, "R": 0.62}

_SEVERITY_BANDS = (
    (9.0, "critical"), (7.0, "high"), (4.0, "medium"), (0.1, "low"),
)


def _roundup(x: float) -> float:
    """CVSS 3.1 规范 roundup（FIRST 官方实现，5 位小数中间精度）。"""
    int_input = int(round(x * 100000))
    if int_input % 10000 == 0:
        return int_input / 100000.0
    return (math.floor(int_input / 10000.0) + 1.0) / 10.0


def parse_vector(vector: str) -> dict[str, str]:
    """解析 'AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H' -> 指标字典。"""
    metrics: dict[str, str] = {}
    for part in (vector or "").split("/"):
        part = part.strip()
        if ":" in part:
            k, v = part.split(":", 1)
            metrics[k.strip().upper()] = v.strip().upper()
    return metrics


def base_score(vector: str) -> float:
    """CVSS 3.1 Base Score。向量非法时返回 0.0。"""
    m = parse_vector(vector)
    try:
        av = _AV[m["AV"]]
        ac = _AC[m["AC"]]
        scope_changed = m.get("S") == "C"
        pr = (_PR_CHANGED if scope_changed else _PR_UNCHANGED)[m["PR"]]
        ui = _UI[m["UI"]]
        c, i, a = m["C"], m["I"], m["A"]
    except KeyError:
        return 0.0

    def _val(x: str) -> float:
        return 0.0 if x == "N" else (0.27 if x == "L" else 0.56)

    iss = 1.0 - ((1.0 - _val(c)) * (1.0 - _val(i)) * (1.0 - _val(a)))
    if scope_changed:
        impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15
    else:
        impact = 6.42 * iss
    if impact <= 0:
        return 0.0
    exploitability = 8.22 * av * ac * pr * ui
    if scope_changed:
        return _roundup(min(1.08 * (impact + exploitability), 10.0))
    return _roundup(min(impact + exploitability, 10.0))


def severity_of(vector: str) -> str:
    score = base_score(vector)
    for low, sev in _SEVERITY_BANDS:
        if score >= low:
            return sev
    return "info"


def score_of(vector: str) -> dict:
    return {"score": base_score(vector), "severity": severity_of(vector)}
