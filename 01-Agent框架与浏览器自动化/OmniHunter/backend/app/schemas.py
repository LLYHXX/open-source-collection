"""Pydantic 输入输出模型。"""
from datetime import datetime

from pydantic import BaseModel, Field


# ===== Task =====
class TaskCreate(BaseModel):
    name: str
    mode: str = "EduSRC"
    vuln_types: str = (
        "sql_injection,rce,unauthorized_access,idor,file_upload,"
        "captcha_bypass,backdoor_compromised"
    )
    source: str = "manual"
    collect_method: str = "auto"
    collect_query: str = ""
    manual_targets: str = ""
    max_pages: int = 3
    llm_override: dict = Field(default_factory=dict)
    fofa_override: str = ""


class TaskOut(BaseModel):
    id: str
    name: str
    mode: str
    status: str
    source: str
    collect_method: str
    collect_query: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


# ===== Target =====
class TargetOut(BaseModel):
    id: str
    task_id: str
    url: str
    host: str
    title: str
    org: str
    score: float
    alive: bool | None
    status: str

    class Config:
        from_attributes = True


# ===== Vuln =====
class VulnOut(BaseModel):
    id: str
    task_id: str
    target_url: str
    vuln_type: str
    severity: str
    title: str
    detail: str
    payload: str
    evidence: str
    status: str
    confidence: float
    reviewer_note: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class VulnReview(BaseModel):
    status: str  # approved/rejected/submitted
    severity: str | None = None
    reviewer_note: str = ""


# ===== Agent =====
class AgentMessageOut(BaseModel):
    id: str
    run_id: str
    role: str
    level: str
    content: str
    tool: str
    tool_result: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


# ===== Intel =====
class IntelOut(BaseModel):
    id: str
    kind: str
    key: str
    value: str
    confidence: float
    hits: int
    lifecycle: str

    class Config:
        from_attributes = True


# ===== Setting =====
class SettingUpdate(BaseModel):
    key: str
    value: str


class AssetPlatformTestIn(BaseModel):
    """资产测绘平台连通性测试请求。"""
    platform: str  # fofa / quake / hunter / zoomeye / shodan / censys
    query: str = ""  # 留空用平台默认测试语句


class AndroidImageInstall(BaseModel):
    """安卓系统镜像安装请求（sdkmanager 包名）。"""
    pkg: str


class AndroidAvdCreate(BaseModel):
    """创建安卓虚拟机（AVD），硬件参数可自定义。"""
    name: str
    image: str  # system-images;android-30;google_apis;x86_64
    memory_mb: int = 2048   # 256~16384
    cores: int = 2          # 1~16
    width: int = 1080
    height: int = 2340
    density: int = 440


class AndroidAvdStart(BaseModel):
    """启动 AVD 参数。"""
    headless: bool = False          # 无界面模式（服务器部署用）
    proxy: bool = True              # 挂 mitmproxy 抓包代理
    proxy_port: int = 8082
    install_cert: bool = True       # 自动 root + 装 mitmproxy CA 到系统证书
    memory_mb: int | None = None    # 覆盖创建时的配置
    cores: int | None = None


class AndroidAppLaunch(BaseModel):
    """APP 启动/卸载请求。"""
    serial: str       # 如 emulator-5554
    package: str      # 如 com.example.app
    activity: str = ""


class PocExpandIn(BaseModel):
    """POC 扩展分析请求（持续挖掘）。"""
    target_url: str            # 目标站点（用于 SSRF 校验与子目标过滤）
    poc_text: str              # POC 描述（含 http URL 或 curl 命令）
    match_regex: str = ""      # 命中判定正则（响应特征），留空只报可达性
    task_id: str = ""          # 提供时确认漏洞自动入库


class SettingOut(BaseModel):
    key: str
    value: str

    class Config:
        from_attributes = True


# ===== Schedule 定时任务 =====
class ScheduleCreate(BaseModel):
    name: str
    task_template: dict = Field(default_factory=dict)  # 复用 TaskCreate 字段
    cron_expr: str = ""  # 优先；如 "0 2 * * *"
    interval_minutes: int = 1440  # 无 cron 时按分钟间隔
    deadline_days: int = 30  # 期限天数，到期自动停


class ScheduleExtend(BaseModel):
    extend_days: int = 30  # 延期天数


class ScheduleOut(BaseModel):
    id: str
    name: str
    task_template: dict
    cron_expr: str
    interval_minutes: int
    start_at: datetime | None = None
    deadline: datetime | None = None
    enabled: bool
    last_run: datetime | None = None
    next_run: datetime | None = None
    run_count: int
    created_at: datetime | None = None

    class Config:
        from_attributes = True


# ===== ReportTemplate 漏洞报告模板 =====
class ReportTemplateCreate(BaseModel):
    name: str
    content: str = ""
    is_default: bool = False


class ReportTemplateUpdate(BaseModel):
    name: str | None = None
    content: str | None = None
    is_default: bool | None = None


class ReportTemplateOut(BaseModel):
    id: str
    name: str
    content: str
    is_default: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ReportGenerate(BaseModel):
    task_id: str
    template_id: str | None = None  # 不填用默认模板


# ===== 通用 =====
class StandardResponse(BaseModel):
    success: bool = True
    message: str = ""
    data: dict | list | None = None
