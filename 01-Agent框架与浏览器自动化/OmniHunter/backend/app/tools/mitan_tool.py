"""密探 mitan 资产测绘工具（03 安全武器）。

mitan 是 MCP Server（39 个工具），覆盖资产测绘/端口/漏洞。
完整接入需在 Trae/客户端配置 mitan MCP server。

MVP 实现：mitan_assets 检测 MCP 可用性并给出配置指引，
未配置时返回友好提示，不阻塞流程；预留子进程调用方式。
"""
import os


def mitan_assets(query: str, limit: int = 50, timeout: int = 60) -> str:
    """资产测绘：通过 mitan MCP 查询资产。

    完整 MCP 接入流程（推荐）：
      1. 本地启动 mitan MCP 服务（见 03-渗透测试与逆向工程/安全测试工具/mitan）
      2. 在 Trae 设置 → MCP 添加 mitan server 配置
      3. aififteen Hunter 通过 MCP 协议调用其 39 个工具

    本适配器为 MVP：检测环境变量 MITAN_MCP_READY 标志，
    未配置时返回配置指引，便于流程跑通。
    """
    # 检测是否已配置 mitan MCP（环境变量标志位由部署方设置）
    ready = os.getenv("MITAN_MCP_READY", "")
    if not ready:
        return (
            "mitan MCP 未配置。完整资产测绘需接入 mitan MCP Server（39 工具）。\n"
            "配置步骤：\n"
            "  1) 启动 mitan MCP 服务（见 03-渗透测试与逆向工程/安全测试工具/mitan）\n"
            "  2) 在 Trae 设置 → MCP 添加 mitan server 配置\n"
            "  3) 设置环境变量 MITAN_MCP_READY=1 表示已就绪\n"
            f"本次查询意图: {query}（limit={limit}）已记录，配置后可重试。"
        )

    # MCP 就绪时：通过子进程或 MCP 客户端调用（此处保持轻量，预留扩展）
    try:
        import subprocess
        from . import which
        exe = which("mitan") or os.getenv("MITAN_BIN", "")
        if not exe:
            return "MITAN_MCP_READY 已设置但未找到 mitan 可执行文件，请设置 MITAN_BIN 环境变量。"
        out = subprocess.run(
            [exe, "search", "-q", query, "-l", str(limit)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
        return (out.stdout or out.stderr or "").strip() or "mitan 无输出"
    except subprocess.TimeoutExpired:
        return f"mitan 超时({timeout}s)"
    except Exception as e:  # noqa: BLE001
        return f"mitan 调用失败: {e}"
