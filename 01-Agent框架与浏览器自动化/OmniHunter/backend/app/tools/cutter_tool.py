"""Cutter 逆向分析工具（03 逆向武器）。

Cutter 是 C++ 二进制逆向分析 CLI（Rizin/Radare2 前端）。
支持 -a analyze 等子命令，输出函数/字符串/反汇编。

需先安装 Cutter 并把可执行文件加入 PATH。未安装时返回友好提示。
"""
import subprocess

from . import which


def cutter_analyze(binary_path: str, action: str = "info",
                   timeout: int = 120) -> str:
    """逆向分析二进制文件。

    action 可选:
      info    - 基本信息（架构/字节/入口，等价 rizin -q -c iI）
      funcs   - 函数列表（r2 -q -c afl）
      strings - 提取字符串（r2 -q -c izz）
      disasm  - 入口点反汇编
    """
    exe = which("Cutter") or which("cutter") or which("rizin") or which("r2")
    if not exe:
        return ("Cutter/rizin 未安装。安装:\n"
                "  Cutter: https://github.com/rizinorg/cutter/releases\n"
                "  rizin : pip install rizin 或系统包管理器")
    if not binary_path:
        return "请提供要分析的二进制文件路径。"

    # rizin CLI 命令映射（Cutter 底层即 rizin）
    cmd_map = {
        "info": ["-q", "-c", "iI", binary_path],
        "funcs": ["-q", "-c", "afl", binary_path],
        "strings": ["-q", "-c", "izz", binary_path],
        "disasm": ["-q", "-c", "pdf @e", binary_path],
    }
    args = cmd_map.get(action, cmd_map["info"])
    try:
        out = subprocess.run(
            [exe, *args], capture_output=True, text=True, timeout=timeout,
        )
        text = out.stdout or out.stderr or ""
        return text.strip() or f"Cutter({action}) 无输出"
    except subprocess.TimeoutExpired:
        return f"Cutter 分析超时({timeout}s)，二进制可能过大，请增大 timeout。"
    except Exception as e:  # noqa: BLE001
        return f"Cutter 错误: {e}"
