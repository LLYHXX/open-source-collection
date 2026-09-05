"""AgentReach 网页/内容抓取工具（02 爬虫武器）。

AgentReach 是 Python CLI（agent-reach 命令），可读网页/YouTube/RSS 等，
转为 LLM 友好文本。

未安装时降级到 Jina Reader（r.jina.ai）兜底，保证基本可用。
"""
import subprocess

from . import which


def agentreach_fetch(url: str, timeout: int = 60) -> str:
    """抓取 URL 内容转 LLM 友好文本。

    优先用 agent-reach CLI；未装则用 Jina Reader 兜底。
    """
    exe = which("agent-reach")
    if exe:
        try:
            out = subprocess.run(
                [exe, "fetch", url], capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=timeout,
            )
            text = (out.stdout or out.stderr or "").strip()
            if text:
                return text
        except subprocess.TimeoutExpired:
            return f"agent-reach 超时({timeout}s)"
        except Exception as e:  # noqa: BLE001
            # 失败则继续走兜底
            pass

    # 兜底：Jina Reader（https://r.jina.ai/URL）
    return _jina_reader(url, timeout)


def _jina_reader(url: str, timeout: int = 60) -> str:
    try:
        import httpx
        r = httpx.get(f"https://r.jina.ai/{url}", timeout=timeout,
                      headers={"X-Return-Format": "markdown"})
        if r.status_code >= 400:
            return (f"agent-reach 未安装，Jina Reader 兜底也失败 "
                    f"({r.status_code})。安装: pip install agent-reach")
        return r.text.strip() or "Jina Reader 无内容"
    except ImportError:
        return ("agent-reach 未安装，且 httpx 不可用（Jina 兜底失败）。\n"
                "安装任一: pip install agent-reach 或 pip install httpx")
    except Exception as e:  # noqa: BLE001
        return f"agent-reach 未安装，Jina Reader 兜底失败: {e}"
