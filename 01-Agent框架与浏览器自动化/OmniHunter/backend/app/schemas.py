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
    status: str | None = None  # 仅内部 Miner 使用；用户默认留空=pending；合法值: pending/pending_approval/rejected


class TaskOut(BaseModel):
    id: str
    name: str
    mode: str
    status: str
    error: str = ""
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
    source: str = ""
    tags: list[str] = []
    masked: bool = False
    created_at: str = ""
    updated_at: str = ""

    class Config:
        from_attributes = True


class IntelIn(BaseModel):
    """新增 / 编辑情报条目。"""
    kind: str = ""
    key: str = ""
    value: str = ""
    confidence: float = 0.6
    source: str = ""
    lifecycle: str = "active"
    tags: list[str] = []


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


# ===== CVE 库 =====
class CveEntryOut(BaseModel):
    id: str
    cve_id: str
    source: str
    title: str
    description: str
    affected: dict = {}
    cvss_score: float = 0.0
    cvss_severity: str = ""
    cvss_vector: str = ""
    published_at: datetime | None = None
    updated_at_src: datetime | None = None
    references: list = []
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class CveListParams(BaseModel):
    """CVE 列表查询：支持关键字/严重等级/分页。"""
    keyword: str = ""
    severity: str = ""  # LOW/MEDIUM/HIGH/CRITICAL
    page: int = 1
    page_size: int = 20


class CveRefreshIn(BaseModel):
    """手动刷新 CVE 库。"""
    days: int = 7       # 拉取最近 N 天的 CVE
    source: str = "all"  # nvd / osv / all


class CveSearchAssetIn(BaseModel):
    """按 CVE 搜未修复资产。"""
    cve_id: str
    platforms: list[str] = []   # 空=已配置全部平台
    max_results: int = 100


class CveScanIn(BaseModel):
    """基于 CVE 命中资产触发挖掘流水线。"""
    cve_id: str
    hit_ids: list[str] = []   # 空=所有 pending 命中资产
    pipeline: str = "engine"  # engine / collab / traffic


class CveAssetHitOut(BaseModel):
    id: str
    cve_id: str
    task_id: str = ""
    url: str
    host: str
    port: int
    title: str
    platform: str
    query: str
    scan_status: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


# ===== 单站协作（权限发现专项）=====
class CollabStartIn(BaseModel):
    """单站协作启动参数。"""
    url: str
    admin_cookie: str = ""
    user_cookie: str = ""
    anon_probe: bool = True           # 是否测未授权访问
    extra_sessions: dict = {}          # 附加身份会话
    enable_engine: bool = True        # 是否并行跑自研引擎
    enable_attacker: bool = True      # 是否跑 LLM 攻击 Agent
