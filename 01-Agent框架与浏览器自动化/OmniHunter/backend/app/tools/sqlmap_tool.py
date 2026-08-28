"""sqlmap SQL 注入检测工具。

安全说明：使用 list 形式传参（非 shell=True），避免命令注入。
"""
import subprocess

from . import which


def scan(url: str, data: str = "", cookie: str = "", timeout: int = 240) -> str:
    exe = which("sqlmap")
    if not exe:
        return "sqlmap 未安装。安装: pip install sqlmap"
    cmd = [exe, "-u", url, "--batch", "--level=1", "--risk=1", "--output-dir=/tmp/omnihunter-sqlmap"]
    if data:
        cmd += ["--data", data]
    if cookie:
        cmd += ["--cookie", cookie]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        text = out.stdout or out.stderr or ""
        return text.strip() or "sqlmap 无输出"
    except subprocess.TimeoutExpired:
        return f"sqlmap 超时({timeout}s)"
    except Exception as e:  # noqa: BLE001
        return f"sqlmap 错误: {e}"
