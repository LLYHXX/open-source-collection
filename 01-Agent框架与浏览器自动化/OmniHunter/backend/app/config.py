"""全局配置：借鉴 AutoHunter 的环境变量体系，扩展浏览器/记忆/规划相关项。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # === LLM（大模型：关键决策层）===
    # protocol=openai 兼容所有 OpenAI 兼容端点：
    #   DeepSeek / 通义Qwen / Kimi / 智谱GLM / OpenRouter / 硅基流动 /
    #   Ollama(http://127.0.0.1:11434/v1) / LM Studio / Gemini OpenAI 兼容端点
    # protocol=anthropic 走 Claude 官方 messages 协议（base_url 填主域，默认 https://api.anthropic.com）
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    llm_protocol: str = "openai"  # openai / anthropic
    tool_compat: str = "auto"  # auto / prompt / native

    # === LLM 小模型层（低 Token 轻量分析；留空回退大模型）===
    llm_small_api_key: str = ""
    llm_small_base_url: str = ""
    llm_small_model: str = ""
    llm_small_protocol: str = "openai"  # openai / anthropic

    # === 资产测绘 ===
    fofa_key: str = ""
    fofa_base_url: str = "https://fofa.info"
    quake_key: str = ""
    hunter_key: str = ""
    zoomeye_key: str = ""
    shodan_key: str = ""
    censys_key: str = ""

    # === 平台 ===
    # 程序化访问令牌；不设则本地免密、公网须密码登录（不再"开放访问"）
    api_token: str = ""
    host_port: int = 18800
    database_url: str = "sqlite:///./data/aififteen_hunter.db"
    # 受信反向代理 IP（逗号分隔）；为空则不信任 X-Forwarded-For，
    # 直接用直连对端 IP 判定本地/公网。反向代理部署时需填代理 IP，
    # 否则所有公网请求会被判为本地从而绕过密码保护。
    trusted_proxies: str = ""

    # === Worker 调度（借鉴 LoopX quota / 关卡）===
    worker_concurrency: int = 3
    worker_step_budget: int = 40  # 单目标最大步数
    worker_timeout: int = 1800  # 单目标超时秒
    reviewer_strict: bool = True  # 极理性初审

    # === 浏览器自动化（借鉴 Nanobrowser）===
    browser_enabled: bool = True
    browser_headless: bool = True

    # === 安全 ===
    waf_enabled: bool = True
    cors_origins: str = "*"
    api_docs_enabled: bool = True
    miner_debug_routes: bool = False
    miner_cron_expr: str = "0 2 * * *"

    # === 自研检测引擎（engine/）===
    engine_plugin_timeout: int = 300  # 单插件 detect/verify 总超时秒
    engine_request_timeout: int = 10  # 单请求超时秒
    engine_max_concurrency: int = 4   # 插件并发数
    engine_weakpwd_enabled: bool = False  # 弱口令探测（有副作用，默认关）
    engine_upload_probe: bool = False     # 上传探测（有副作用，默认关）

    # 持续挖掘（信息泄露自动深挖）
    engine_followup_enabled: bool = True  # 确认信息泄露后自动提取子目标递归扫描
    engine_max_depth: int = 2             # follow-up 最大递归深度（1=只挖一层）
    followup_max_urls: int = 50           # 单任务 follow-up URL 总量上限（防失控）

    # === CVE 库（自动更新 + 资产搜索）===
    nvd_api_key: str = ""                 # NVD API Key（无 key 限速 5/30min，有 key 50/30min）
    cve_fetch_enabled: bool = True        # 启动定时拉取 CVE
    cve_fetch_cron: str = "0 2 * * *"     # CVE 拉取 cron（默认每日 02:00）
    cve_fetch_days: int = 7               # 每次拉取最近 N 天
    cve_fetch_max: int = 500              # 单次最大拉取条数
    cve_auto_scan_enabled: bool = False   # 自动扫描命中资产（有副作用，默认关）
    cve_auto_scan_cron: str = "0 3 * * *" # 自动扫描 cron（默认每日 03:00）
    cve_auto_scan_pipeline: str = "engine"  # 自动扫描流水线：engine / collab
    cve_auto_scan_max: int = 10            # 单次自动扫描资产数上限

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def trusted_proxy_list(self) -> list[str]:
        return [o.strip() for o in self.trusted_proxies.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def apply_dynamic_overrides(overrides: dict[str, str] | None) -> list[str]:
    """把动态配置（Setting 表键值）覆盖到当前 settings 实例，立即生效。

    键不区分大小写（统一小写后匹配字段名）；未知键忽略。
    值按字段类型转换（str/int/float/bool），转换失败丢弃该键。
    返回成功应用的键列表。
    """
    s = get_settings()
    fields = type(s).model_fields
    applied: list[str] = []
    for k, v in (overrides or {}).items():
        name = str(k).strip().lower()
        if name not in fields:
            continue
        try:
            ann = fields[name].annotation
            if ann is bool:
                setattr(s, name, str(v).strip().lower() in ("1", "true", "yes", "on"))
            elif ann is int:
                setattr(s, name, int(str(v).strip()))
            elif ann is float:
                setattr(s, name, float(str(v).strip()))
            else:
                setattr(s, name, str(v))
            applied.append(name)
        except (ValueError, TypeError):
            continue
    return applied
