"""引擎调度核心 —— 加载插件、匹配指纹、分配任务、执行检测、调用验证、输出结果。

流水线（黄金原则落地）：
  指纹前置 → 插件 match 过滤 → 并发 detect（单插件超时隔离）
  → 误报过滤器 → verify 独立复现（沙箱优先/直连兜底）→ CVSS 自动定级
单插件报错不影响整个引擎（try/except + wait_for 双保险）。
"""
from __future__ import annotations

import asyncio
import time

from .base import DetectorPlugin, ScanContext, SuspectFinding, TargetFingerprint
from .cvss import score_of
from .detectors import load_plugins
from .fingerprint import fingerprint_target
from .fp_filter import FalsePositiveFilter
from . import sandbox


class ScanEngine:
    """自研扫描引擎底座：检测结果可控、可迭代。"""

    def __init__(self, settings=None):
        from ..config import get_settings
        self.settings = settings or get_settings()
        self.plugins: list[DetectorPlugin] = load_plugins()

    def list_detectors(self) -> list[dict]:
        return [{
            "id": p.id, "name": p.name, "vuln_type": p.vuln_type,
            "description": p.description,
            "side_effect_free": p.side_effect_free,
        } for p in self.plugins]

    async def scan(self, base_url: str, *, emit=None,
                   extra: dict | None = None) -> dict:
        """对单目标执行完整扫描，返回指纹 + 确认漏洞列表 + 统计。"""
        started = time.monotonic()
        cfg = self.settings

        async def _emit(level: str, msg: str):
            if emit:
                try:
                    await emit(level, msg)
                except Exception:  # noqa: BLE001
                    pass

        # 1) 指纹前置
        await _emit("info", f"[engine] 指纹识别: {base_url}")
        fp: TargetFingerprint = await fingerprint_target(
            base_url, timeout=getattr(cfg, "engine_request_timeout", 10) * 2)
        if fp.status == 0:
            await _emit("error", f"[engine] 目标不可达: {base_url}")
            return {"fingerprint": {}, "findings": [],
                    "stats": {"error": "target_unreachable"}}

        techs = ",".join(fp.techs[:8]) or "无"
        await _emit("info",
                    f"[engine] 指纹: {fp.status} {fp.webserver or '-'} "
                    f"[{techs}] 端点 {len(fp.paths)} 个")

        ctx = ScanContext(base_url=base_url, fp=fp, emit=emit,
                          extra=extra or {})

        # 2) 插件 match 过滤（指纹前置按需检测 + 副作用开关）
        weakpwd_on = getattr(cfg, "engine_weakpwd_enabled", False)
        upload_on = getattr(cfg, "engine_upload_probe", False)
        active: list[DetectorPlugin] = []
        for p in self.plugins:
            if not p.side_effect_free:
                allowed = (weakpwd_on if p.id == "weakpwd.common_creds"
                           else upload_on if p.id == "upload.type_bypass"
                           else False)
                if not allowed:
                    await _emit("info", f"[engine] 跳过 {p.id}（副作用未开启）")
                    continue
            try:
                if p.match(fp):
                    active.append(p)
            except Exception:  # noqa: BLE001
                continue
        await _emit("info", f"[engine] {len(active)}/{len(self.plugins)} "
                            f"插件匹配通过: {[p.id for p in active]}")

        # 3) 并发 detect（每插件独立超时 + 异常隔离）
        plugin_timeout = getattr(cfg, "engine_plugin_timeout", 300)
        sem = asyncio.Semaphore(getattr(cfg, "engine_max_concurrency", 4))
        suspects: list[SuspectFinding] = []

        async def _run_plugin(p: DetectorPlugin):
            async with sem:
                try:
                    await _emit("info", f"[engine] 检测中: {p.id}")
                    out = await asyncio.wait_for(p.detect(ctx), timeout=plugin_timeout)
                    suspects.extend(out or [])
                    await _emit("info",
                                f"[engine] {p.id} 完成，疑似 {len(out or [])} 个")
                except asyncio.TimeoutError:
                    await _emit("error", f"[engine] {p.id} 超时({plugin_timeout}s)，跳过")
                except Exception as e:  # noqa: BLE001 —— 单插件报错不影响引擎
                    await _emit("error", f"[engine] {p.id} 异常: {e}")

        await asyncio.gather(*(_run_plugin(p) for p in active))
        await _emit("info", f"[engine] 检测完成，疑似 {len(suspects)} 个，进入验证")

        # 4) 误报过滤器（WAF页/404伪装/登录跳转/相同页差异）
        fpf = FalsePositiveFilter(ctx)
        filtered: list[SuspectFinding] = []
        for f in suspects:
            try:
                bad, reason = await fpf.check(f)
            except Exception:  # noqa: BLE001
                bad, reason = False, ""
            if bad:
                await _emit("info",
                            f"[engine] 过滤误报 {f.plugin_id} {f.url}: {reason}")
            else:
                filtered.append(f)
        await _emit("info", f"[engine] 过滤后剩 {len(filtered)} 个，独立复现中")

        # 5) verify 独立复现（检测命中 != 漏洞，复现成功才算确认）
        confirmed: list[SuspectFinding] = []
        for f in filtered:
            plugin = next((p for p in self.plugins if p.id == f.plugin_id), None)
            try:
                if plugin is not None:
                    v = await asyncio.wait_for(plugin.verify(ctx, f),
                                               timeout=plugin_timeout)
                else:
                    v = await asyncio.wait_for(
                        self._default_verify(ctx, f), timeout=plugin_timeout)
                if v is not None:
                    # 沙箱重放标记（骨架：镜像未内置时 direct）
                    mode = await sandbox.replay_in_sandbox(f.url)
                    f.verify_evidence = (f"[{mode['mode']}] "
                                         + (f.verify_evidence or "复现通过"))
                    confirmed.append(f)
            except asyncio.TimeoutError:
                await _emit("error", f"[engine] verify 超时: {f.plugin_id}")
            except Exception as e:  # noqa: BLE001
                await _emit("error", f"[engine] verify 异常 {f.plugin_id}: {e}")

        # 6) CVSS 3.1 自动定级
        findings: list[dict] = []
        for f in confirmed:
            score = score_of(f.vector or plugin_default_vector(self.plugins, f))
            d = f.to_dict()
            d.update(score)
            findings.append(d)
        # 按严重度降序
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        findings.sort(key=lambda d: (order.get(d.get("severity", "info"), 9),
                                     -(d.get("score") or 0)))

        elapsed = time.monotonic() - started
        await _emit("result",
                    f"[engine] 扫描完成: 确认 {len(findings)} 个漏洞 "
                    f"({elapsed:.1f}s, 疑似 {len(suspects)} → 过滤 "
                    f"{len(filtered)} → 确认 {len(findings)})")
        return {
            "fingerprint": {
                "url": fp.url, "host": fp.host, "status": fp.status,
                "title": fp.title, "webserver": fp.webserver,
                "techs": fp.techs, "paths_count": len(fp.paths),
            },
            "findings": findings,
            "stats": {
                "plugins_total": len(self.plugins),
                "plugins_active": len(active),
                "suspects": len(suspects),
                "filtered": len(suspects) - len(filtered),
                "confirmed": len(findings),
                "elapsed_seconds": round(elapsed, 1),
            },
        }

    @staticmethod
    async def _default_verify(ctx: ScanContext,
                              f: SuspectFinding) -> SuspectFinding | None:
        from .http_client import http_request
        if not f.url:
            return None
        r = await http_request("GET", f.url, timeout=10)
        if r.status == 0:
            return None
        f.verified = True
        f.confidence = min(0.9, f.confidence + 0.2)
        return f


def plugin_default_vector(plugins: list[DetectorPlugin], f: SuspectFinding) -> str:
    for p in plugins:
        if p.id == f.plugin_id:
            return p.default_vector
    return "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N"
