"""aififteen Hunter 自研检测引擎 —— 从「工具调用器」到「有自己规则的扫描引擎」。

使用：
    from ..engine import ScanEngine, register_engine_tools
    engine = ScanEngine(settings)
    result = await engine.scan("https://target.com", emit=emit)
"""
from __future__ import annotations

from .base import DetectorPlugin, ScanContext, SuspectFinding, TargetFingerprint
from .cvss import base_score, severity_of
from .scheduler import ScanEngine


def register_engine_tools(reg, settings) -> None:
    """把引擎注册进 ToolRegistry，Worker/Agent 可像普通武器一样调用。

    ToolRegistry.execute 为同步调用，而引擎是 async —— 用独立线程 +
    独立事件循环桥接（agent 的 async 上下文中 run_until_complete 会报错）。
    """
    import asyncio
    import threading

    engine = ScanEngine(settings)
    total_timeout = getattr(settings, "engine_plugin_timeout", 300) * 2

    def _run_async(coro, timeout: float) -> dict:
        box: dict = {"value": {"error": f"engine scan 超时({timeout}s)"}}

        def _runner():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                box["value"] = loop.run_until_complete(coro)
            except Exception as e:  # noqa: BLE001
                box["value"] = {"error": f"engine 异常: {e}"}
            finally:
                loop.close()

        t = threading.Thread(target=_runner, daemon=True)
        t.start()
        t.join(timeout=timeout)
        return box["value"]

    def _engine_scan(url: str, admin_cookie: str = "",
                     user_cookie: str = "") -> dict:
        """url: 目标地址；admin_cookie/user_cookie: 越权检测身份会话（可选）。"""
        async def _scan():
            extra = {}
            if admin_cookie or user_cookie:
                extra["sessions"] = {"admin": {"cookie": admin_cookie},
                                     "user": {"cookie": user_cookie}}
            return await engine.scan(url, extra=extra)

        return _run_async(_scan(), timeout=total_timeout)

    reg.register(
        "engine_scan", _engine_scan,
        "自研检测引擎：指纹前置+10类漏洞确定性检测+独立验证+CVSS定级"
        "（SQLi/XSS/RCE/遍历/SSRF/信息泄露/上传/弱口令/IDOR/越权）",
        {"type": "object",
         "properties": {
             "url": {"type": "string"},
             "admin_cookie": {"type": "string", "default": ""},
             "user_cookie": {"type": "string", "default": ""},
         },
         "required": ["url"]},
    )

    reg.register(
        "engine_list_detectors", lambda: {"detectors": engine.list_detectors()},
        "列出引擎已加载的检测插件（id/名称/类型/是否无副作用）",
        {"type": "object", "properties": {}},
    )


__all__ = [
    "ScanEngine", "DetectorPlugin", "ScanContext",
    "SuspectFinding", "TargetFingerprint", "base_score", "severity_of",
    "register_engine_tools",
]
