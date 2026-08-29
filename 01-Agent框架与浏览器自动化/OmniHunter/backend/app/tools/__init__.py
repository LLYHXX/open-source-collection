"""工具装配：注册命令行挖洞工具链（借鉴 AutoHunter 内置工具链）。

工具未安装时返回友好提示而非崩溃，便于在无工具环境调试流程。
"""
import shutil


def register_all(reg, settings) -> None:
    from . import (
        agentreach_tool,
        anti_waf_tool,
        asset_tool,
        bettercap_tool,
        code_audit_tool,
        crypto_tool,
        cutter_tool,
        httpx_tool,
        mitan_tool,
        nmap_tool,
        nuclei_tool,
        payload_tool,
        reverse_tool,
        sqlmap_tool,
        traffic_tool,
        web_tools,
    )

    # === 命令行挖洞工具链（借鉴 AutoHunter）===
    reg.register(
        "httpx_probe", httpx_tool.probe,
        "探活与基础指纹：返回状态码/标题/技术栈/webserver",
        {"type": "object",
         "properties": {"url": {"type": "string"}},
         "required": ["url"]},
    )
    reg.register(
        "nmap_scan", nmap_tool.scan,
        "端口与服务版本扫描（默认 top ports，可指定端口如 80,443,8080）",
        {"type": "object",
         "properties": {"host": {"type": "string"}, "ports": {"type": "string"}},
         "required": ["host"]},
    )
    reg.register(
        "nuclei_scan", nuclei_tool.scan,
        "nuclei 漏洞模板扫描（可指定模板类别如 cves,exposures）",
        {"type": "object",
         "properties": {"url": {"type": "string"}, "templates": {"type": "string"}},
         "required": ["url"]},
    )
    reg.register(
        "sqlmap_scan", sqlmap_tool.scan,
        "sqlmap SQL 注入检测（data 为 POST body，cookie 可选）",
        {"type": "object",
         "properties": {
             "url": {"type": "string"},
             "data": {"type": "string"},
             "cookie": {"type": "string"},
         },
         "required": ["url"]},
    )

    # === 02 爬虫武器（Firecrawl / AgentReach）===
    reg.register(
        "web_scrape", web_tools.web_scrape,
        "Firecrawl 抓取单个 URL 转 LLM 友好 markdown（需 FIRECRAWL_API_KEY）",
        {"type": "object",
         "properties": {"url": {"type": "string"}, "api_key": {"type": "string"}},
         "required": ["url"]},
    )
    reg.register(
        "web_search", web_tools.web_search,
        "Firecrawl 按关键词搜索网页（需 FIRECRAWL_API_KEY）",
        {"type": "object",
         "properties": {
             "query": {"type": "string"},
             "limit": {"type": "integer"},
             "api_key": {"type": "string"},
         },
         "required": ["query"]},
    )
    reg.register(
        "agentreach_fetch", agentreach_tool.agentreach_fetch,
        "AgentReach 抓取网页/YouTube/RSS 转 LLM 文本（未装则 Jina Reader 兜底）",
        {"type": "object",
         "properties": {"url": {"type": "string"}},
         "required": ["url"]},
    )

    # === 03 安全武器（bettercap / 密探 mitan）===
    reg.register(
        "bettercap_api", bettercap_tool.bettercap_api,
        "bettercap REST API：网络探测/ARP/host 查询（需启动 bettercap）",
        {"type": "object",
         "properties": {
             "action": {"type": "string"},
             "target": {"type": "string"},
             "api_url": {"type": "string"},
             "token": {"type": "string"},
         },
         "required": ["action"]},
    )
    reg.register(
        "mitan_assets", mitan_tool.mitan_assets,
        "密探 mitan 资产测绘（MCP Server 39 工具，未配置给配置指引）",
        {"type": "object",
         "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
         "required": ["query"]},
    )

    # === 03 逆向武器（Cutter）===
    reg.register(
        "cutter_analyze", cutter_tool.cutter_analyze,
        "Cutter/rizin 逆向分析：info/funcs/strings/disasm",
        {"type": "object",
         "properties": {
             "binary_path": {"type": "string"},
             "action": {"type": "string"},
         },
         "required": ["binary_path"]},
    )

    # === 流量驱动业务逻辑漏洞挖掘工具（AI2 Attacker 核心，mitmproxy）===
    reg.register(
        "start_traffic_capture", traffic_tool.start_traffic_capture,
        "开启 mitmproxy 流量监听录制 flows（AI2 攻击探测端核心）："
        "需将浏览器/客户端 HTTP/HTTPS 代理指向 127.0.0.1:proxy_port",
        {"type": "object",
         "properties": {
             "proxy_port": {"type": "integer", "default": 8082},
             "duration": {"type": "integer", "default": 60},
         }},
    )
    reg.register(
        "get_captured_traffic", traffic_tool.get_captured_traffic,
        "读取已录制的流量摘要（method+url+status+关键 headers+body 片段），"
        "聚焦隐形参数（Authorization/Cookie/X-Token/状态校验位）。建议先 stop 再读全量",
        {"type": "object",
         "properties": {
             "filter": {"type": "string"},
             "max_items": {"type": "integer", "default": 50},
         }},
    )
    reg.register(
        "stop_traffic_capture", traffic_tool.stop_traffic_capture,
        "主动停止 mitmproxy 流量监听，返回 flow 文件路径",
        {"type": "object", "properties": {}},
    )

    # === 03 纯 Python 内置武器（借鉴 reverse-skill / DeepEye / Strix）===
    # 逆向分析：lief 解析 + capstone 反汇编 + 正则提字符串，无需 Cutter/rizin/IDA
    reg.register(
        "binary_info", reverse_tool.binary_info,
        "纯 Python 逆向：lief 解析 PE/ELF/Mach-O，输出架构/入口/节区/导入表/导出表",
        {"type": "object",
         "properties": {"binary_path": {"type": "string"}},
         "required": ["binary_path"]},
    )
    reg.register(
        "disasm", reverse_tool.disasm,
        "纯 Python 反汇编：capstone 多架构（x86/x64/arm/mips），"
        "arch 留空自动探测，start_addr 起始偏移，count 反汇编条数",
        {"type": "object",
         "properties": {
             "binary_path": {"type": "string"},
             "arch": {"type": "string"},
             "start_addr": {"type": "integer", "default": 0},
             "count": {"type": "integer", "default": 50},
         },
         "required": ["binary_path"]},
    )
    reg.register(
        "extract_strings", reverse_tool.extract_strings,
        "纯 Python 提字符串：正则提取 ASCII + UTF-16LE，"
        "标记 URL/IP/注册表/敏感 API 等可疑串",
        {"type": "object",
         "properties": {
             "binary_path": {"type": "string"},
             "min_len": {"type": "integer", "default": 4},
         },
         "required": ["binary_path"]},
    )

    # 资产侦察：crt.sh + dnspython 子域名 + 纯 socket 端口扫描，nmap/subfinder 兜底
    reg.register(
        "subdomain_enum", asset_tool.subdomain_enum,
        "纯 Python 子域名枚举：crt.sh 证书透明度 + dnspython A 记录解析",
        {"type": "object",
         "properties": {"domain": {"type": "string"}, "limit": {"type": "integer", "default": 50}},
         "required": ["domain"]},
    )
    reg.register(
        "port_scan_basic", asset_tool.port_scan_basic,
        "纯 Python 端口扫描：socket TCP connect 并发，nmap 未装兜底，"
        "开放端口抓 banner 猜服务",
        {"type": "object",
         "properties": {
             "host": {"type": "string"},
             "ports": {"type": "string", "default": "22,80,443,3306,8080,8443"},
             "timeout": {"type": "integer", "default": 2},
             "workers": {"type": "integer", "default": 50},
         },
         "required": ["host"]},
    )

    # Payload 模板库：Strix 思想——优先加载已有 payload，避免 LLM 凭空猜测
    reg.register(
        "payload_library", payload_tool.payload_library,
        "内置 payload 模板库（SQLi/XSS/SSRF/命令注入/IDOR/业务逻辑），"
        "按 vuln_type + category 查询；无参列出全部索引",
        {"type": "object",
         "properties": {
             "vuln_type": {"type": "string"},
             "category": {"type": "string"},
         }},
    )

    # === 白盒代码审计武器（借鉴 reverse-skill code-audit skill，纯 Python）===
    reg.register(
        "bandit_scan", code_audit_tool.bandit_scan,
        "白盒 Bandit 静态扫描 Python 源码：硬编码密钥/命令注入/SQL 拼接等 B1xx 告警",
        {"type": "object",
         "properties": {
             "target_path": {"type": "string"},
             "severity": {"type": "string", "default": "low"},
             "confidence": {"type": "string", "default": "low"},
             "recursive": {"type": "boolean", "default": True},
         },
         "required": ["target_path"]},
    )
    reg.register(
        "dlint_scan", code_audit_tool.dlint_scan,
        "白盒 Dlint 扫 Python 危险调用（eval/exec/pickle.load/system 等 DUO 规则）",
        {"type": "object",
         "properties": {
             "target_path": {"type": "string"},
             "recursive": {"type": "boolean", "default": True},
         },
         "required": ["target_path"]},
    )
    reg.register(
        "code_audit_summary", code_audit_tool.code_audit_summary,
        "白盒一站式审计：Bandit+Dlint 合并摘要 + 严重度统计，给 CodeAuditor 调用",
        {"type": "object",
         "properties": {
             "target_path": {"type": "string"},
             "severity": {"type": "string", "default": "low"},
         },
         "required": ["target_path"]},
    )

    # === 前端加密参数处理（解决 3DES/AES 等加密导致流量变异失效）===
    reg.register(
        "analyze_crypto_js", crypto_tool.analyze_crypto_js,
        "静态分析前端 JS 识别加密调用（CryptoJS/forge），提取 key/iv/algo/mode",
        {"type": "object",
         "properties": {"js_source": {"type": "string"}},
         "required": ["js_source"]},
    )
    reg.register(
        "generate_js_hook", crypto_tool.generate_js_hook,
        "生成动态 JS Hook 脚本（混淆代码用），在加密前修改明文让前端原生加密算密文",
        {"type": "object",
         "properties": {
             "crypto_func_name": {"type": "string"},
             "mutation": {"type": "object"},
         },
         "required": ["crypto_func_name"]},
    )
    reg.register(
        "decrypt_and_reencrypt", crypto_tool.decrypt_and_reencrypt,
        "离线解密→明文变异→重加密（已知 key 的 AES/3DES/DES，需 pycryptodome）",
        {"type": "object",
         "properties": {
             "ciphertext": {"type": "string"},
             "key": {"type": "string"},
             "algo": {"type": "string", "default": "AES"},
             "mode": {"type": "string", "default": "CBC"},
             "iv": {"type": "string", "default": ""},
             "mutation": {"type": "object"},
         },
         "required": ["ciphertext", "key"]},
    )

    # === 轻量对抗防护（WAF 检测/速率自适应/退避/隐蔽头）===
    reg.register(
        "detect_waf", anti_waf_tool.detect_waf,
        "从响应特征识别常见 WAF（阿里云盾/Cloudflare/安全狗/长亭雷池等 12+）",
        {"type": "object",
         "properties": {
             "response_text": {"type": "string"},
             "headers": {"type": "object"},
         }},
    )
    reg.register(
        "adaptive_rate", anti_waf_tool.adaptive_rate,
        "根据响应状态历史自适应调整并发速率（429/403 降速，2xx 恢复）",
        {"type": "object",
         "properties": {
             "status_history": {"type": "array", "items": {"type": "integer"}},
             "base_qps": {"type": "number", "default": 5.0},
         },
         "required": ["status_history"]},
    )
    reg.register(
        "retry_with_backoff", anti_waf_tool.retry_with_backoff,
        "指数退避重试策略（被 WAF/速率限制拦截时用）",
        {"type": "object",
         "properties": {
             "attempt": {"type": "integer", "default": 1},
             "base_delay": {"type": "number", "default": 1.0},
             "max_delay": {"type": "number", "default": 60.0},
         }},
    )
    reg.register(
        "build_stealth_headers", anti_waf_tool.build_stealth_headers,
        "生成隐蔽请求头（轮换 UA/Referer/Accept-Language，降低 WAF 识别为扫描器）",
        {"type": "object",
         "properties": {"url": {"type": "string"},
                          "referer": {"type": "string"}}},
    )
    reg.register(
        "waf_bypass_payload_hints", anti_waf_tool.waf_bypass_payload_hints,
        "WAF 绕过 payload 提示（sqli/xss/cmd_injection 内联注释/编码/分块等）",
        {"type": "object", "properties": {"vuln_type": {"type": "string"}}},
    )

    # === 自研检测引擎（确定性规则优先，LLM 只做兜底）===
    from ..engine import register_engine_tools
    register_engine_tools(reg, settings)


def which(name: str) -> str | None:
    return shutil.which(name)
