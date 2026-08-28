"""Site Profiler 单站深挖自动收集 Agent。

用户需求：「单站深挖自动收集」——给一个根域/URL，自动跑全套资产收集：
  1) subdomain_enum（crt.sh + dnspython 子域名枚举）
  2) port_scan_basic（纯 socket 端口扫描，nmap 未装兜底）
  3) httpx_probe（每个活子域探活+指纹）
  4) web_scrape / agentreach_fetch（关键入口页面抓正文，给 Modeler 建模）

输出统一资产清单（subdomains / open_ports / web_entries / fingerprint），
沉淀进 Intel(kind="site_profile")，下次同站直接 recall 复用不烧 token。
"""
import json
from typing import Any, Callable
from urllib.parse import urlparse

from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient
from ..core.tool_registry import ToolRegistry


def _root_domain(url: str) -> str:
    """从 url 提取根域（用于 subdomain_enum 与经验沉淀 site_key）。"""
    try:
        host = urlparse(url).hostname or url
    except Exception:  # noqa: BLE001
        host = url
    host = host.lower().strip()
    for p in ("http://", "https://"):
        if host.startswith(p):
            host = host[len(p):]
    host = host.split("/")[0].split(":")[0]
    # 取最后两段作根域（example.com / example.co.jp 简化处理）
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def _host(url: str) -> str:
    try:
        return urlparse(url).hostname or url
    except Exception:  # noqa: BLE001
        return url


class SiteProfilerAgent(BaseAgent):
    role = "site_profiler"
    description = ("单站深挖自动收集：子域名+端口+web 入口+指纹，"
                   "沉淀 site_profile 进记忆供下次复用。")

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None, memory: Any = None,
                 on_event: Callable[..., None] | None = None):
        super().__init__(run_id, target=target, llm=llm, tools=tools,
                         memory=memory, on_event=on_event)

    async def run(self, task_input: dict) -> dict:
        url = self.target.url
        root = _root_domain(url)
        self.think(f"单站深挖自动收集: root={root}, url={url}")

        # 命中缓存直接复用（用户要求：第二次直接读取，不重复烧 token）
        if self.memory:
            cached = self.memory.recall_latest("site_profile", key=root)
            if cached is not None:
                self.memory.hit_by_kind_key("site_profile", root)
                self.think(f"命中 site_profile 缓存(#{cached.hits}次复用)，直接读取不重跑")
                try:
                    profile = json.loads(cached.value)
                    profile["_from_cache"] = True
                    return profile
                except Exception:  # noqa: BLE001
                    self.think("缓存解析失败，重新收集")

        profile: dict[str, Any] = {
            "root_domain": root,
            "primary_url": url,
            "subdomains": [],
            "open_ports": [],
            "web_entries": [],
            "fingerprint": "",
        }

        # 1) 子域名枚举
        sub_out = self.tools.execute("subdomain_enum",
                                      {"domain": root, "limit": 50})
        self.tool_call("subdomain_enum", {"domain": root}, sub_out[:500])
        subs = self._parse_subdomains(sub_out, root)
        profile["subdomains"] = subs
        self.think(f"枚举到 {len(subs)} 个活子域")

        # 2) 端口扫描（主域）
        host = _host(url)
        port_out = self.tools.execute(
            "port_scan_basic",
            {"host": host, "ports": "22,80,443,3306,6379,8080,8443,9200"})
        self.tool_call("port_scan_basic", {"host": host}, port_out[:500])
        profile["open_ports"] = self._parse_ports(port_out, host)

        # 3) httpx 探活 + 指纹（主域 + 前 3 个子域，避免太慢）
        candidates = [url] + [f"http://{s}" for s in subs[:3]]
        fps: list[str] = []
        for u in candidates:
            fp = self.tools.execute("httpx_probe", {"url": u})
            self.tool_call("httpx_probe", {"url": u}, fp[:200])
            if fp and "未安装" not in fp:
                fps.append(fp)
                # 第一个有效指纹作为主指纹
                if not profile["fingerprint"]:
                    profile["fingerprint"] = fp
        profile["web_entries"] = fps[:5]

        # 4) 关键入口页面正文（给 Modeler 建模用）
        if self.tools and "web_scrape" in self.tools.names():
            scrape = self.tools.execute("web_scrape", {"url": url})
            self.tool_call("web_scrape", {"url": url},
                           (scrape or "")[:300])
            if scrape and "未配置" not in scrape and "未安装" not in scrape:
                profile["entry_markdown"] = scrape[:2000]

        # 5) 沉淀 site_profile 进记忆（下次复用不烧 token）
        if self.memory:
            self.memory.store("site_profile", root,
                              json.dumps(profile, ensure_ascii=False),
                              confidence=0.85,
                              source=f"site_profiler:{self.target.id}")
            self.think(f"沉淀 site_profile 进记忆，下次同站直接复用")

        profile["_from_cache"] = False
        return profile

    def _parse_subdomains(self, sub_out: str, root: str) -> list[str]:
        """从 subdomain_enum 输出解析子域列表。"""
        if not sub_out or "未解析" in sub_out:
            return []
        subs: list[str] = []
        for line in sub_out.splitlines():
            line = line.strip()
            if not line or line.startswith("=") or line.startswith("--"):
                continue
            # 形如 "  api.example.com  -> 1.2.3.4"
            if " -> " in line:
                name = line.split(" -> ", 1)[0].strip()
                if name and root in name and name not in subs:
                    subs.append(name)
            elif root in line and " " not in line.strip():
                if line not in subs:
                    subs.append(line)
        return subs

    def _parse_ports(self, port_out: str, host: str) -> list[dict]:
        """从 port_scan_basic 输出解析开放端口列表。"""
        if not port_out or "open=0" in port_out:
            return []
        ports: list[dict] = []
        for line in port_out.splitlines():
            line = line.strip()
            if not line or line.startswith("=") or line.startswith("--"):
                continue
            # 形如 "  80/tcp open  http banner='HTTP/1.1 200 OK'"
            if "/tcp" in line and "open" in line:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        port = int(parts[0].split("/")[0])
                    except ValueError:
                        continue
                    svc = parts[2] if len(parts) > 2 else "unknown"
                    banner = ""
                    if "banner=" in line:
                        banner = line.split("banner=", 1)[1].strip("'\"")
                    ports.append({"port": port, "service": svc,
                                  "banner": banner})
        return ports
