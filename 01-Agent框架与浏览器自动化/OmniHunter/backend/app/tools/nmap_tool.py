"""nmap 端口与服务扫描工具。"""
import subprocess

from . import which


def scan(host: str, ports: str = "", timeout: int = 120) -> str:
    exe = which("nmap")
    if not exe:
        return "nmap 未安装。请用系统包管理器安装 nmap。"
    cmd = [exe, "-sV", "--open", "-Pn"]
    if ports:
        cmd += ["-p", ports]
    else:
        cmd += ["--top-ports", "200"]
    cmd.append(host)
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return (out.stdout or out.stderr or "").strip() or "nmap 无输出"
    except subprocess.TimeoutExpired:
        return f"nmap 超时({timeout}s)"
    except Exception as e:  # noqa: BLE001
        return f"nmap 错误: {e}"
