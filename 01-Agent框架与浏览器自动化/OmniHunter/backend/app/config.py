"""全局配置：借鉴 AutoHunter 的环境变量体系，扩展浏览器/记忆/规划相关项。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # === LLM ===
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    llm_protocol: str = "auto"  # auto / openai_chat / anthropic_messages
    tool_compat: str = "auto"  # auto / prompt / native

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

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def trusted_proxy_list(self) -> list[str]:
        return [o.strip() for o in self.trusted_proxies.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
