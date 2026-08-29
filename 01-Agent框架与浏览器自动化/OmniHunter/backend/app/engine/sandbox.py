"""独立验证沙箱骨架 —— 隔离环境重放，排除环境因素误报。

MVP 骨架行为：
- 检测 docker 可用 + 沙箱镜像存在 → 沙箱重放（预留接口，当前透传直连）
- 不可用 → 降级直连重放（verifier 的既有行为），并标记 mode=direct
后续填实：内置通用靶机镜像、流量在沙箱内重放对比。
"""
from __future__ import annotations

import shutil
import subprocess


def docker_available() -> bool:
    exe = shutil.which("docker")
    if not exe:
        return False
    try:
        return subprocess.run([exe, "info"], capture_output=True,
                              timeout=10).returncode == 0
    except Exception:  # noqa: BLE001
        return False


def sandbox_image_available(image: str = "aififteen/sandbox:latest") -> bool:
    if not docker_available():
        return False
    try:
        out = subprocess.run(["docker", "images", "-q", image],
                             capture_output=True, text=True, timeout=15)
        return bool((out.stdout or "").strip())
    except Exception:  # noqa: BLE001
        return False


async def replay_in_sandbox(payload_url: str, method: str = "GET",
                            image: str = "aififteen/sandbox:latest") -> dict:
    """在沙箱容器内重放请求。返回 {"mode": "sandbox"|"direct", ...}。

    骨架：沙箱镜像未内置时直接标记 direct（由插件原 verify 兜底）。
    """
    if sandbox_image_available(image):
        # TODO: 后续填实 —— docker run --network none 镜像内 curl 重放
        return {"mode": "sandbox", "image": image, "url": payload_url}
    return {"mode": "direct", "url": payload_url}
