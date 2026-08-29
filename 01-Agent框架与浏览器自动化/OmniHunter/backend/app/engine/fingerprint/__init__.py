"""指纹前置层 —— 永远不要全量插件跑所有目标，先识别指纹再匹配插件。

优先级：
1. Go 编译二进制 engine/golang/bin/fp_scanner(.exe)（subprocess 调 JSON）
2. Python 兜底实现 py_fp（httpx 探活 + 组件指纹 + 端点发现）
"""
from __future__ import annotations

import os
import subprocess
import sys

from .py_fp import python_fingerprint


def _go_binary() -> str | None:
    base = os.path.dirname(os.path.abspath(__file__))
    exe = "fp_scanner.exe" if sys.platform == "win32" else "fp_scanner"
    path = os.path.join(base, "..", "golang", "bin", exe)
    return path if os.path.isfile(path) else None


async def fingerprint_target(base_url: str, timeout: int = 20) -> "TargetFingerprint":
    from ..base import TargetFingerprint

    exe = _go_binary()
    if exe:
        try:
            out = subprocess.run(
                [exe, "-url", base_url, "-timeout", str(timeout)],
                capture_output=True, text=True, timeout=timeout + 10,
            )
            data = __import__("json").loads(out.stdout or "{}")
            if data.get("host"):
                return TargetFingerprint(
                    url=data.get("url", base_url),
                    host=data["host"], scheme=data.get("scheme", "http"),
                    port=int(data.get("port", 0)),
                    status=int(data.get("status", 0)),
                    title=data.get("title", ""),
                    webserver=data.get("webserver", ""),
                    techs=list(data.get("techs", [])),
                    paths=list(data.get("paths", [])),
                )
        except Exception:  # noqa: BLE001 —— Go 二进制失败静默降级 Python
            pass
    fp = await python_fingerprint(base_url, timeout=timeout)
    return fp or TargetFingerprint(url=base_url)
