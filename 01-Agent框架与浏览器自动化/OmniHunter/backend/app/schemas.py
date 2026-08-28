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
