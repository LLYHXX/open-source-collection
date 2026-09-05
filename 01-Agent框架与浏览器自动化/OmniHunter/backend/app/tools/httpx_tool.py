"""httpx 探活与指纹工具。"""
import subprocess

from . import which


def probe(url: str, timeout: int = 30) -> str:
    exe = which("httpx")
    if not exe:
        return "httpx 未安装。安装: go install github.com/projectdiscovery/httpx/cmd/httpx@latest"
    cmd = [exe, "-silent", "-title", "-tech-detect", "-status-code",
           "-web-server", "-no-color", url]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return (out.stdout or out.stderr or "").strip() or "httpx 无输出"
    except subprocess.TimeoutExpired:
        return f"httpx 超时({timeout}s)"
    except Exception as e:  # noqa: BLE001
        return f"httpx 错误: {e}"
