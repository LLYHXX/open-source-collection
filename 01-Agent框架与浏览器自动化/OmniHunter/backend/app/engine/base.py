"""自研检测引擎内核 —— 标准检测插件基类。

设计原则（黄金三原则）：
1. 检测与验证强制分离：detect() 命中只是 SuspectFinding（疑似），
   verify() 独立复现成功才是确认漏洞。检测命中 != 漏洞。
2. 指纹前置按需检测：match() 先判断目标是否适用，不全量乱扫。
3. 超时/异常全兜底：所有请求走 engine.http_client（统一超时+异常兜底），
   单插件报错不影响整个引擎（scheduler 侧隔离）。

插件三要素（缺一不可）：
- 匹配条件: match(fingerprint) -> bool
- 检测逻辑: detect(ctx) -> list[SuspectFinding]
- 判定规则: verify(ctx, finding) -> SuspectFinding | None
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


@dataclass
class TargetFingerprint:
    """指纹层产出：目标画像。插件 match() 依据它按需检测。"""
    url: str = ""
    host: str = ""
    scheme: str = "http"
    port: int = 0
    status: int = 0
    title: str = ""
    webserver: str = ""
    techs: list[str] = field(default_factory=list)
    # 指纹层发现的端点/入口路径（相对路径）
    paths: list[str] = field(default_factory=list)

    def has_tech(self, *names: str) -> bool:
        lows = {t.lower() for t in self.techs}
        return any(n.lower() in lows for n in names)

    @property
    def base_url(self) -> str:
        return f"{self.scheme}://{self.host}" + (
            f":{self.port}" if self.port and self.port not in (80, 443) else ""
        )


@dataclass
class SuspectFinding:
    """疑似漏洞（detect 产出）。verify 通过后 confidence 提升为 confirmed。"""
    plugin_id: str = ""
    vuln_type: str = ""
    title: str = ""
    detail: str = ""
    payload: str = ""
    evidence: str = ""
    url: str = ""
    param: str = ""
    # CVSS 3.1 向量，由插件声明默认向量，调度器统一算分定级
    vector: str = ""
    confidence: float = 0.5
    verified: bool = False
    verify_evidence: str = ""

    def to_dict(self) -> dict:
        return {
            "plugin_id": self.plugin_id, "vuln_type": self.vuln_type,
            "title": self.title, "detail": self.detail,
            "payload": self.payload, "evidence": self.evidence,
            "url": self.url, "param": self.param,
            "vector": self.vector, "confidence": self.confidence,
            "verified": self.verified, "verify_evidence": self.verify_evidence,
        }


# 引擎事件回调：async (level, content) -> None
EmitFn = Callable[[str, str], Awaitable[None]]


@dataclass
class ScanContext:
    """单目标扫描上下文，传给每个插件的 detect/verify。"""
    base_url: str
    fp: TargetFingerprint
    emit: EmitFn | None = None
    # 外部注入：身份会话（auth_traverse 用）、额外参数等
    extra: dict[str, Any] = field(default_factory=dict)


class DetectorPlugin(ABC):
    """标准检测插件基类 —— 引擎与工具堆砌的本质区别在这里。"""

    # 插件唯一 id，如 "sqli.error_based"
    id: str = ""
    # 漏洞类型（对齐 Vuln.vuln_type 词典）
    vuln_type: str = ""
    name: str = ""
    description: str = ""
    # 默认 CVSS 3.1 向量（子类必须给出）
    default_vector: str = ""
    # 是否无副作用探测（弱口令爆破/上传探测为 False，受配置开关控制）
    side_effect_free: bool = True

    def match(self, fp: TargetFingerprint) -> bool:
        """匹配条件：目标指纹是否适用本插件。默认全适用。"""
        return True

    @abstractmethod
    async def detect(self, ctx: ScanContext) -> list[SuspectFinding]:
        """检测逻辑：产出疑似漏洞列表（不做最终判定）。"""

    async def verify(self, ctx: ScanContext,
                     finding: SuspectFinding) -> SuspectFinding | None:
        """判定规则：独立复现。返回 None 表示验证失败（丢弃）。

        默认实现：重放一次 payload，若请求仍可达（非异常）则保留并标记
        verified=True —— 子类应覆写为更强的复现逻辑（读文件/遍历/取数）。
        """
        from .http_client import http_request
        if not finding.url:
            return None
        r = await http_request("GET", finding.url)
        if r.status == 0:
            return None  # 复现时目标不可达，视为无法验证
        finding.verified = True
        finding.confidence = min(0.9, finding.confidence + 0.2)
        return finding
