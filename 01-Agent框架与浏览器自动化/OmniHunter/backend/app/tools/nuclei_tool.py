"""nuclei 漏洞模板扫描工具。"""
import subprocess

from . import which


def scan(url: str, templates: str = "", timeout: int = 180) -> str:
    exe = which("nuclei")
    if not exe:
        return "nuclei 未安装。安装: go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
    cmd = [exe, "-u", url, "-silent", "-no-color", "-nc"]
    if templates:
        cmd += ["-tags", templates]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (out.stdout or out.stderr or "").strip() or "nuclei 无输出（未命中模板）"
    except subprocess.TimeoutExpired:
        return f"nuclei 超时({timeout}s)"
    except Exception as e:  # noqa: BLE001
        return f"nuclei 错误: {e}"
